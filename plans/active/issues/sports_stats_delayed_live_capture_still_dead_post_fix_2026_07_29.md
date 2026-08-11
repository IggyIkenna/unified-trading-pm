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
    /plans/archive/2026_08/sports_live_availability_and_source_latency_2026_07_24.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-07-29
author: unknown
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
context_scope:
  [
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    unified-api-contracts/unified_api_contracts/registry/venue_adapter_keys.py,
    unified-api-contracts/unified_api_contracts/canonical/domain/sports/provider_league_ids.py,
    deployment-service/deployment_service/sports_latency_observation.py,
    unified-trading-library/unified_trading_library/manifest_writer/_read_index.py,
  ]
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
- [x] ✅ [INFRA] P1. **NEW, opened by the correction above.** Trace why `FOOTYSTATS`/`UNDERSTAT`/`TRANSFERMARKT`/
      `SOCCER_FOOTBALL_INFO`/`OPEN_METEO` appear in the `venues` argument passed to
      `urdi_reference_provider.fetch_instruments_for_all_venues()` for a live sports dispatch at all, given they are NOT
      in `VENUES_BY_ASSET_GROUP["sports"]` — find the call site that builds `active_venues` for sports (likely a "core
      entity"/"Date filter" completeness pass, given the one execution log I traced this to was entity-scoped to
      `LINEUPS`) and either exclude these 5 enrichment-provider names from that list (they were never meant to be
      URDI-fetchable "venues") or confirm there's a reason they're intentionally included that this pass didn't surface.
      **Done when**: a fresh day-plus of live Cloud Run Job logs for `uts-prod-instruments-service-sports-fixtures`
      shows zero `URDI fetch: N venue(s) failed with PERMANENT errors` lines mentioning any of these 5. Repo:
      instruments-service. — **Root cause traced + fixed 2026-07-29 (slot 7, infra).** Found the exact call site:
      `instruments_service/engine/orchestrator/venue_core.py`'s `get_venues_for_asset_groups()` DELIBERATELY appends all
      5 enrichment-provider names into the sports venue list it returns (lines ~488-497, own docstring: "IS owns
      reference-data providers API_FOOTBALL/FOOTYSTATS/UNDERSTAT/TRANSFERMARKT/SOCCER_FOOTBALL_INFO/OPEN_METEO...
      Decision C (operator 2026-06-29): two separate registries") — this is `process.py::process_instruments`'s
      `active_venues`, confirmed by its own pre-existing `_fixtures_fetch_failed()` docstring
      (`api_football_fixtures_fetch_failed_false_positive_2026_07_13`): "`active_venues` for a sports run also carries
      the ENRICHMENT-ONLY pseudo-venues ... these are fetched later, in stage 7 enrichment, and are NEVER part of this
      stage-4 URDI instruments fetch." **So the inclusion in `active_venues` itself is intentional** (stage-7
      `process_enrichment.py` and stage-4 `process_zero_records.py` both do `"UNDERSTAT" in active_venues_set`-style
      membership checks against it, and `process_completeness.py` independently already excludes these same 5 names from
      its own `expected_venues` for an analogous reason — root-cause-fixed
      `api_football_write_path_blank_data_type_2026_07_13`). **The actual bug**: `process_fetch.py::_fetch_urdi_records`
      — the function that builds the `defi_active`/`non_defi_active` split and calls
      `fetch_instruments_for_all_venues()` — never filtered these 5 names out before splitting/fetching, so on every
      dispatch where `skip_urdi=False` (any sports entity NOT in `_ENRICHMENT_ONLY_ENTITIES`/`_PER_FIXTURE_ENTITIES` —
      e.g. `TEAMS`/`STANDINGS`/`INJURIES`/`TRANSFERS`/`FIXTURES` itself), all 5 names flowed straight into
      `fetch_instruments_for_all_venues(venues=...)`, which correctly flags them `unsupported` (their
      `VENUE_TO_ADAPTER_KEY` entries are `NO_ADAPTER_YET` sentinels, per this doc's item-1 fix) and logs the
      `No URDI adapter for N venue(s)` WARNING + `URDI fetch: N venue(s) failed with PERMANENT errors` ERROR every time.
      **Fix**: excluded the existing, already-canonical `_ENRICHMENT_PROVIDERS` frozenset (defined in
      `process_preflight.py` — exactly these 5 names, used elsewhere for the `--sports-provider` short-circuit) from
      `active_venues` inside `_fetch_urdi_records`, before the defi/non-defi split — `API_FOOTBALL` (the one real
      URDI-fetchable sports venue) is untouched since it's not in that set. `non_error_venues`/completeness behaviour is
      UNCHANGED (these 5 venues were never in `non_error_venues` before either, since they were always classified
      `failed`/`unsupported` — verified by reading
      `_non_error_venues.update(... if v not in {e.venue for e in ...failed_venues}...)`). Added a focused regression
      test (`tests/unit/test_process_fetch_enrichment_venue_exclusion.py`) asserting `fetch_instruments_for_all_venues`
      is called with exactly `["API_FOOTBALL"]` when `active_venues` includes all 5 enrichment names, plus a control
      case for `skip_urdi=True`. Ran the full related unit suites (`test_orchestrator_process.py`,
      `test_orchestrator_gaps.py`, `test_orchestrator_coverage.py`, `test_new_orchestrator.py`,
      `test_urdi_reference_provider.py`) green (218 passed), then full `quality-gates.sh` green (100s,
      `.qg_last_passed_sha=fcabadd1`). Shipped: `instruments-service@12c176f8` via quickmerge to `live-defi-rollout`.
      **Residual — this todo's own literal done-when (a day-plus of clean prod logs) is NOT yet verified** (the fix only
      just landed) — that observation naturally falls out of the `[VERIFY] P1` todo directly below once its own day-plus
      gate is reached; no separate todo needed since it already re-checks this exact issue chain on the same cadence.
      If, once verified, the `No URDI adapter`/`URDI fetch...failed` lines for these 5 venues persist despite this fix,
      that would mean a THIRD, still-undiagnosed emission path — escalate rather than assume this fix alone closes the
      doc.
- [x] ✅ [VERIFY] P1. **Depends on the todo above landing + redeploying (or on confirming no fix is needed).** After a
      full day-plus of live operation post-that-fix, re-run this doc's Step 3 manifest query (`data_type=XG`,
      `capture_status=captured`, `written_at` > the new redeploy cutoff, `pipeline_mode != batch_understat`) — confirm a
      fresh row appears (closes this issue) or, if still zero, escalate further (a fourth cause would remain). **Also
      confirms item-2's own done-when** (added 2026-07-29 alongside item-2's fix, `instruments-service@12c176f8`): over
      that same day-plus window, `gcloud logging read` for `uts-prod-instruments-service-sports-fixtures` should show
      ZERO `No URDI adapter for N venue(s)` / `URDI fetch: N venue(s) failed with PERMANENT errors` lines mentioning
      `FOOTYSTATS`/`UNDERSTAT`/`TRANSFERMARKT`/ `SOCCER_FOOTBALL_INFO`/`OPEN_METEO` — if any persist post-`12c176f8`,
      that is a THIRD, separate emission path (escalate, don't assume item-2's fix alone explains a residual). Repo:
      instruments-service / market-tick-data-service (read-only). — **Checked 2026-07-29T03:50Z-04:00Z (slot 5,
      data_engineering): premature, both this todo's own gates are still open, not the "confirming no fix is needed"
      escape hatch.** (1) Item-2 (the `active_venues` trace above) has NOT landed — grepped `instruments-service` for
      any commit since `2026-07-29T00:00Z` touching `urdi_reference_provider`/`active_venues`: none. (2) Only ~2h20m
      elapsed since the item-1 sentinel fix shipped (`unified-api-contracts@6186be5a`, `2026-07-29T01:30:49Z`) vs. the
      "day-plus of live operation" this todo requires — re-running Step 3 now is a checkpoint, not a verdict, either
      way. **Attempted the escape hatch anyway** (confirm item-2's fix isn't needed by checking whether a real
      XG-entity-scoped dispatch ever hits the adapter-key error) — **inconclusive, do not treat as resolved**: a single
      direct execution trace (`03:51:33-03:51:50Z`, `Sports entity filter from CLI: XG`) showed ZERO
      `No URDI adapter`/`URDI fetch...failed` lines — that execution instead logged
      `Per-fixture enrichment: 39 fixtures x 0 entities = 0 calls queued` (same "0 calls queued" pattern the parent
      doc's Step-3 investigation already flagged). But a bulk nearest-preceding-line correlation over the last ~10h of
      logs (137 `No URDI adapter` occurrences) attributed 48/137 to a preceding `XG` entity-filter line — the two
      signals conflict because the Cloud Run Job runs multiple entities as CONCURRENT subprocesses whose log lines
      interleave (e.g. `XG` and `FIXTURE_STATS` entity-filter lines land within the same second in the combined log), so
      "nearest preceding line" is not a valid per-execution correlation without a trace/PID discriminator — exactly the
      gap item-2's own scope already flagged ("out of scope for this read-only verification pass"). **New finding for
      whoever picks up item-2**: one clean, non-interleaved trace (`03:26:21-03:26:42Z`) DOES show the error firing
      directly after `LEAGUES`/`INJURIES`/ `TRANSFERS` entity-filter lines, immediately followed by
      `Date filter <date>: N instruments active (from URDI fetch)` — confirms the doc's own hypothesis that this is a
      shared "core entity"/venue-universe completeness check, not something scoped to a single specific entity; worth
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
      `/skip-current-task {"reason_code": "GATED"}`. Next dispatch: same condition as above. — **Checked
      2026-07-29T15:19Z (slot 15, worker): still premature, both gates open, bare check only (no manifest re-query, per
      the prior check's own guidance)**. Confirmed item-2 still NOT landed:
      `git log --since="2026-07-29T00:00:00Z" --all -- '*urdi_reference_provider*' '*active_venues*'` in
      instruments-service (HEAD `42dd7a14`) returns zero commits. Current time (`15:19Z`) still well before the day-plus
      fallback gate (`2026-07-30T01:31Z`, ~10h away). No change since the 14:12Z check. Releasing via
      `/skip-current-task {"reason_code": "GATED"}`. Next dispatch: same condition as above. — **Checked
      2026-07-29T20:07Z (slot 4, data_engineering): item-2 IS now confirmed landed AND deployed — correcting the prior 5
      bare checks' false negative — but the day-plus gate is still open (reset to a later target).** All 5 prior "item-2
      NOT landed" checks (03:50Z-15:19Z) used `git log ... -- '*urdi_reference_provider*' '*active_venues*'`, which
      never matches the file item-2 actually touched (`instruments_service/engine/orchestrator/process_fetch.py` —
      confirmed via `git show --stat 12c176f8`); those checks' own tooling was too narrow for the real fix location, not
      a sign the fix was actually absent. Re-ran with `-- '*process_fetch*'` and it finds `12c176f8`, committed
      **2026-07-29T14:20:16Z** — i.e. item-2 landed BEFORE even the 15:19Z check; that check's negative was a
      glob-pattern gap, not reality. **Deploy confirmed**: the currently running
      `uts-prod-instruments-service-sports-fixtures` Cloud Run Job image (tag `4c05f2d`, digest `sha256:3e8feb1…`, built
      **2026-07-29T18:02:00Z**) has `12c176f8` as an ancestor (`git merge-base --is-ancestor 12c176f8 4c05f2d` → yes),
      and a fresh execution (`…-wnnl6`, started `20:06:33Z`) confirms that image is actively running now — so item-2's
      real redeploy cutoff is **`2026-07-29T18:02:00Z`**, not the item-1 fallback used above. **Day-plus gate reset**:
      only ~2h05m elapsed since that cutoff at check time (`20:07Z`) — nowhere near "a full day-plus of live operation
      post-that-fix". New target: **not before `2026-07-30T18:02Z`** (supersedes the old item-1-fallback target of
      `2026-07-30T01:31Z`, which no longer applies now that item-2 has a real cutoff of its own). Did NOT re-run the
      Step-3 manifest query or the `gcloud logging read` sweep for the 5 enrichment-venue error lines — with only ~2h of
      post-deploy operation, either would be a very-early checkpoint at best, not a verdict, and the doc's own
      established pattern (03:50Z entry) already covers what an early checkpoint looks like. Releasing via
      `/skip-current-task {"reason_code": "GATED"}`. Next dispatch: once `2026-07-30T18:02Z` passes, re-run BOTH the
      Step-3 manifest query AND the `gcloud logging read` sweep for real — this is the first check where both gates
      (item-2 landed AND item-2 deployed) are actually satisfied, so the next check is positioned to deliver the real
      verdict, not another bare/early checkpoint. — **Checked 2026-07-29T23:25Z (slot 9, data_engineering): still
      premature, bare check only (no manifest re-query, per the prior check's own guidance).** Confirmed no further
      relevant change: `instruments-service` HEAD (`7f272911`) has zero commits touching `*process_fetch*` since
      `2026-07-29T18:00:00Z` — nothing has moved past the already-confirmed `12c176f8`/`4c05f2d` deploy. Current time
      (`23:25Z`) is still ~18.6h before the day-plus gate (`2026-07-30T18:02Z`). No change since the 20:07Z check.
      Releasing via `/skip-current-task {"reason_code": "GATED"}`. Next dispatch: same condition as above — once
      `2026-07-30T18:02Z` passes, re-run both the Step-3 manifest query and the `gcloud logging read` sweep for the real
      verdict. — **Checked 2026-07-30T00:29Z (slot 11, data_engineering): still premature, bare check only (no manifest
      re-query, per the prior check's own guidance).** Confirmed no further relevant change: instruments-service HEAD
      (`7f272911`, `origin/live-defi-rollout`) unchanged since the 23:25Z check — zero commits touching
      `*process_fetch*` since `2026-07-29T18:00:00Z`. Current time (`2026-07-30T00:29Z`) is still ~17.5h before the
      day-plus gate (`2026-07-30T18:02Z`). No change since the 23:25Z check. Releasing via
      `/skip-current-task {"reason_code": "GATED"}`. Next dispatch: same condition as above — once `2026-07-30T18:02Z`
      passes, re-run both the Step-3 manifest query and the `gcloud logging read` sweep for the real verdict. —
      **Checked 2026-07-30T10:54Z (slot 5, data_engineering): still premature, bare check only (no manifest re-query,
      per the prior check's own guidance).** Confirmed no further relevant change: instruments-service HEAD (`695c399b`,
      `origin/live-defi-rollout`) has zero commits touching `*process_fetch*` since `2026-07-29T18:00:00Z` — the only
      new commit since the last check (`695c399b`) is an unrelated docstring correction in
      `repair_tradfi_instrument_type_counts.py`. Current time (`10:54Z`) is still ~7h08m before the day-plus gate
      (`2026-07-30T18:02Z`). No change since the 00:29Z check. Releasing via
      `/skip-current-task {"reason_code": "GATED"}`. Next dispatch: same condition as above — once `2026-07-30T18:02Z`
      passes, re-run both the Step-3 manifest query and the `gcloud logging read` sweep for the real verdict. —
      **Checked 2026-07-30T11:59Z (slot 8, review): still premature, bare check only (no manifest re-query, per the
      prior check's own guidance).** Confirmed no further relevant change: instruments-service HEAD (`cccc6ef5`,
      `origin/live-defi-rollout`) has zero commits touching `*process_fetch*` since `2026-07-29T18:00:00Z` — unchanged
      from the 10:54Z check's deploy state. Current time (`11:59Z`) is still ~6h03m before the day-plus gate
      (`2026-07-30T18:02Z`). No change since the 10:54Z check. Releasing via
      `/skip-current-task {"reason_code": "GATED"}`. Next dispatch: same condition as above — once `2026-07-30T18:02Z`
      passes, re-run both the Step-3 manifest query and the `gcloud logging read` sweep for the real verdict. —
      **Checked 2026-07-31T06:18Z-06:55Z (slot 14, worker): day-plus gate PASSED (2026-07-31T06:18Z, ~12h16m past
      `2026-07-30T18:02Z`) — first real verdict, both original gates now genuinely satisfied. Full re-run done: item-2's
      own gate CONFIRMED CLOSED (zero adapter-key error recurrence); Step-3 manifest STILL zero fresh XG captures — but
      root cause is now identified and it is NOT a code defect (a fourth, benign cause).** 1. **`gcloud logging read`
      sweep, `uts-prod-instruments-service-sports-fixtures`, `timestamp>="2026-07-29T18:02:00Z"` through now (~36h
      window)**: ZERO `No URDI adapter for N venue(s)` / `URDI fetch: N venue(s) failed with PERMANENT errors` lines
      mentioning any of FOOTYSTATS/UNDERSTAT/TRANSFERMARKT/SOCCER_FOOTBALL_INFO/OPEN_METEO. Sanity-checked the query
      itself is valid (same filter minus the timestamp bound returns the pre-fix occurrences, last one at
      `2026-07-29T17:49:26Z` — 13 min before the `18:02:00Z` cutoff, i.e. it stopped exactly at deploy). **Item-2's own
      done-when is CONFIRMED MET.** 2. **Step-3 manifest re-run** (`availability_index.parquet`, `data_type=XG`,
      `capture_status='captured'`, `written_at > '2026-07-29T18:02:00Z'`): **0 rows**, confirmed both with the doc's
      original filter (`pipeline_mode != batch_understat`) AND with that filter DROPPED entirely — same 0-row result
      either way. All 7,714 all-time `captured` XG rows remain 100% `batch_understat`, max `written_at` unchanged at
      `2026-07-22T05:23:36Z`. 3. **Methodology correction (real, but doesn't change the verdict)**: the doc's own
      `pipeline_mode != batch_understat` filter is unsound as a live-vs-batch discriminator. Grepped
      `instruments_service/engine/orchestrator/understat.py`: **every** write from `_fetch_understat_xg` /
      `_run_understat_shots_date` hardcodes `pipeline_mode=PipelineMode.BATCH_UNDERSTAT` unconditionally — it is a
      source-literal, not a live/batch tag. Confirmed both call sites use it identically: `process_preflight.py:317-318`
      (the periodic completeness/"Date filter" sweep) AND `process_enrichment.py:293/306` (the REAL live per-fixture
      `_run_remaining_enrichment` dispatch this whole doc is about) — so a genuine live-triggered capture would ALSO
      show `pipeline_mode=batch_understat`, making the doc's filter unable to ever distinguish the two. Re-ran Step-3
      with the filter dropped (see #2) — result unchanged (still 0), so this flaw did NOT mask a false negative here,
      but future checks of this doc should drop the `pipeline_mode !=` clause entirely and rely on `written_at`
      alone. 4. **Traced the actual dispatch gate** (`process_enrichment.py:291`:
      `if "UNDERSTAT" in active_venues_set and entity_wanted("XG")`) to rule out item-2's own fix having broken it: read
      `process_fetch.py:96-142` (`_fetch_urdi_records`) — the `_ENRICHMENT_PROVIDERS` exclusion builds a NEW local
      `_fetchable_venues` list (line 135); the caller's original `active_venues` parameter is never mutated. So the
      enrichment-stage gate at line 291 is intact and unaffected by item-2's fix — ruled out as the 4th cause. 5. **THE
      ACTUAL FOURTH CAUSE, confirmed via two independent data sources — genuinely benign, not a bug**: Understat only
      covers 5 leagues (`UNDERSTAT_NAMES` in
      `unified-api-contracts/unified_api_contracts/canonical/domain/sports/provider_league_ids.py`:
      `BUNDESLIGA`/`EPL`/`LA_LIGA`/`LIGUE_1`/`SERIE_A`). Downloaded + queried the live `latency_observations` parquet
      index (`day=2026-07-29`..`2026-07-31` shards): **1767** `stats_delayed` trigger fires occurred in the post-cutoff
      window (`recorded_at_utc > '2026-07-29T18:02:00Z'`) — but **ZERO** of them are for any of the 5 Understat-covered
      `league_id` values (the 1767 fires span ROMANIA_CUP/ARGENTINA_PRIMERA/
      BRASILEIRAO/UCL/UECL/KOREAN_FA_CUP/COLOMBIA_CUP/etc. — South American leagues + continental competitions, none of
      which Understat covers). Cross-checked independently via the `availability_index` manifest's own
      `data_type=FIXTURES` rows for the 5 covered leagues: **`instrument_count=0` for every date `2026-07-25` through
      `2026-08-01`** (the manifest's current forward-lookahead ceiling) across all 5 leagues — i.e. there are genuinely
      no scheduled/known fixtures for EPL/Bundesliga/La Liga/Ligue 1/Serie A anywhere in this window (mid-to-late-July
      is these leagues' off-season; 2026-27 season fixtures aren't in the manifest's lookahead window yet). **The live
      pipeline cannot have captured Understat XG data in this window because no Understat-covered-league match ever
      kicked off to fire `stats_delayed` for it — this is a data-availability gap, not a pipeline defect.** Both
      structural fixes (item-1 registry sentinels, item-2 active_venues exclusion) are confirmed deployed and working
      (zero error-log recurrence); the pipeline is validated as far as it CAN be validated without a real covered-league
      match. **Flipping this todo done** — its own done-when ("confirm a fresh row appears... or, if still zero,
      escalate further") is satisfied: escalated, found, and the 4th cause is identified as benign. Added a new
      follow-up todo below (not prose, per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 2) to
      re-verify once a real covered-league fixture exists — that is the first opportunity for genuine end-to-end proof.
- [x] ✅ [INFRA] P2. Persist `FirstSuccessPoller._pending` across `--one-shot` invocations (state-bucket-backed, same
      pattern as `PeriodicTierState`) so `first_success=True` / genuine `fetched_rows` confirmations become structurally
      possible. Lower urgency than the two todos above (observability/confirmation only — does not gate the real
      dispatch). Add a regression test proving a pending entry registered in one `SportsTriggerScheduler` instance is
      picked up and resolved by a FRESH instance reading the same persisted state (simulating the one-shot restart).
      Repo: deployment-service.

      **DONE 2026-07-30 — deployment-service@a172915.** `FirstSuccessPoller` (`sports_latency_observation.py`) now
                                  accepts `bucket`/`key`/`storage` (mirrors `PeriodicTierState`'s exact adapter shape — `default_state_storage()`
                                  promoted from module-private to shared-public for this reuse); loads persisted `_pending` on construction,
                                  persists after every real mutation in `register_from_event()` (only when at least one entity was actually
                                  registered) and `poll()` (only when something was removed/updated) — best-effort, `except Exception` (broadened
                                  from the initially-narrower `(OSError, ValueError)` after discovering it could crash the live dispatch path on a
                                  transient storage failure; persistence must never block a real trigger fire). `SportsTriggerScheduler.__init__`
                                  wires it via a new `_build_first_success_poller()` (same `state_bucket or resolve_state_bucket()` + full-failure
                                  fallback-to-in-memory-only shape as the existing `_build_periodic_state()`). **The regression test asked for is
                                  exactly `test_first_success_poller_survives_fresh_instance_across_one_shot_restart`** (registers on instance A,
                                  discards it, constructs a brand-new instance B against the same bucket/storage, asserts B's `.pending` already
                                  contains the entry with no `register_from_event` call) — plus persist-on-register, persist-on-poll-removal,
                                  malformed-state-starts-fresh, and no-bucket-stays-in-memory-only (back-compat) tests, 5 new tests total in
                                  `tests/unit/test_sports_latency_observation.py`. Found + fixed a real test-isolation gap while wiring this in:
                                  the shared `_make_scheduler_with_recorder()` test helper (used by ~10 pre-existing tests) never overrode
                                  `state_bucket`, so every test sharing the default `resolve_state_bucket()` bucket name was reading/writing the
                                  SAME `CLOUD_MOCK_MODE=true` mock-storage-backed state file — invisible before this change because no prior code
                                  path actually persisted real content there; now scoped to a per-test-unique bucket
                                  (`f"deployment-scripts-test-{uuid.uuid4().hex}"`), fixing a latent cross-test-pollution risk for
                                  `PeriodicTierState` too, not just this new code. Full `quality-gates.sh` green (2967 passed).

- [ ] [VERIFY] P2. **New, opened 2026-07-31 by the VERIFY P1 todo above.** Both structural fixes (venue-adapter-key
      registry sentinels + `active_venues` enrichment-provider exclusion) are confirmed deployed and working (zero
      recurrence of `No URDI adapter`/`URDI fetch...failed` error-log lines mentioning the 5 enrichment venues over a
      36h+ window). But the day-plus live-operation re-check found the reason Step-3's manifest query still shows zero
      fresh Understat XG captures is NOT a code defect: Understat only covers 5 leagues
      (BUNDESLIGA/EPL/LA_LIGA/LIGUE_1/SERIE_A) and all 5 are confirmed in their off-season — zero `stats_delayed`
      trigger fires for any of them in the 36h post-fix window (1767 fires total, all for OTHER leagues), and the
      `availability_index` manifest shows `instrument_count=0` FIXTURES for all 5 leagues through `2026-08-01` (the
      manifest's current forward-lookahead ceiling). The live capture pipeline has therefore never had a real
      opportunity to prove it works end-to-end since the fixes landed. **Done when**: once any of the 5
      Understat-covered leagues has a real fixture whose `stats_delayed` trigger fires live (check via the
      `latency_observations` parquet index, `trigger_name='stats_delayed'` + `league_id` in the 5-league set,
      `recorded_at_utc` after the fixture is confirmed scheduled), re-run Step 3's manifest query (`data_type=XG`,
      `capture_status='captured'`, `written_at` after that fire) — a fresh captured (or honestly `empty_confirmed`, if
      Understat itself has no data for that specific match) row confirms the live pipeline genuinely works end-to-end;
      if it's STILL zero despite a real covered-league match having fired, that would be a genuine fifth cause worth
      escalating. **Also note for whoever picks this up**: the doc's original Step-3 filter
      (`pipeline_mode != batch_understat`) is NOT a reliable live-vs-batch discriminator —
      `instruments_service/engine/orchestrator/understat.py` hardcodes `pipeline_mode=PipelineMode.BATCH_UNDERSTAT` on
      every write regardless of caller (both the periodic completeness sweep AND the real live per-fixture dispatch use
      it identically) — query on `written_at` alone, don't filter on `pipeline_mode`. **Correction (2026-08-10, slot-6):
      every prior check's FIXTURES query used `data_type=="FIXTURES"`, which is a LEGACY data_type frozen at max
      `date=2026-08-01` since ~2026-07-24 (superseded by `instruments_service/triggers/sports_fixtures_daily_repoll.py`,
      Phase B.1 of `instruments_master.md`, which writes the live rolling `[today-1d, today+8d]` window to
      `data_type=="FIXTURES_SCHEDULE"` instead) — use `FIXTURES_SCHEDULE`, not `FIXTURES`, for the lookahead-ceiling
      check going forward; `FIXTURES` may not reflect current reality once it stops being written.** Repo:
      instruments-service (read-only check, no code change expected unless a genuine 5th cause surfaces). — **Checked
      2026-07-31T06:38Z (slot 11, worker): still gated, no covered-league fixture has fired yet.** Queried
      `latency_observations/day={2026-07-29..07-31}` directly via `pandas.read_parquet` against
      `gs://instruments-store-sports-prd-central-element-323112/_index/` (ad-hoc, no committed query script exists for
      this pair of datasets — confirmed via a dedicated tooling search): 1512 `stats_delayed` fires post-cutoff
      (`>2026-07-29T18:02:00Z`, data through `2026-07-31T04:41:54Z`), **zero** for any of the 5 Understat-covered
      `league_id`s (`BUNDESLIGA`/`EPL`/`LA_LIGA`/`LIGUE_1`/`SERIE_A`) — the 1512 span 24 other leagues/cups only.
      Cross-checked `availability_index.parquet`'s `data_type=FIXTURES` rows for the same 5 leagues: forward-lookahead
      ceiling is still `2026-08-01` (unchanged from the 06:18Z-06:55Z check), all rows through that date carry
      `instrument_count=0` (`empty_confirmed`/`attempted_failed`); the last nonzero (`captured`) FIXTURES row for any of
      the 5 leagues is `2026-05-29` (end of the prior season) — confirms still genuinely off-season, not a regression.
      No change since the prior check ~20 min earlier. Releasing via `/skip-current-task {"reason_code": "GATED"}` — the
      done-when (a real covered-league fixture firing `stats_delayed`) is not yet met; this doc does not need
      re-checking on a tight cadence (leagues resume on a season schedule, not within-hour granularity) — next dispatch
      should wait for a longer interval or an operator signal that the new season's fixture list has landed, rather than
      re-polling every few minutes. — **Checked 2026-07-31T08:25Z-08:33Z (slot 7, backend_engineer): still gated, no
      change.** Re-ran both checks via the canonical
      `unified_trading_library.manifest_writer._read_index. read_availability_index()` slim-column path (not raw
      `pd.read_parquet`, per this pass's own tooling research) and a direct GCS blob listing for `latency_observations`:
      (1) FIXTURES rows for the 5 covered leagues — per-league max `date` is still `2026-08-01` (the lookahead ceiling,
      unchanged) with max `instrument_count` unchanged (7-10/league); every nonzero-`instrument_count` row is still
      dated `2026-05-14..2026-05-29` (prior season, same set the 06:18Z check found — no new rows). (2) `stats_delayed`
      fires over `day={2026-07-29..07-31}`: **1512** total (matches the 06:38Z check's count exactly), **zero** for any
      of the 5 covered `league_id`s. Confirms the off-season gate is unchanged ~1h47m after the last check. **Process
      note for main/operator**: this todo has now accumulated 9 "still gated, no change" checks since 2026-07-29T15:19Z
      (03:50Z/05:02Z/09:06Z/14:12Z/15:19Z/20:07Z/23:25Z, 2026-07-30T00:29Z/10:54Z/11:59Z, 2026-07-31T06:18Z/06:38Z, this
      one) at re-dispatch intervals as tight as ~20min-2h, despite every check since 06:18Z explicitly recommending a
      longer interval — a season-schedule condition doesn't change within-day, so each of these re-checks burns a full
      worker dispatch for a guaranteed-identical answer. Recommend main/operator PARK this task server-side
      (`unified-trading-pm/agents/RULES.md` § 4 "Park a task" — `priority: 999` + `priority_override: true` + a
      `prereqs.prerequisites` condition, e.g. `sports-understat-season-active`, flipped `true` once the new season's
      fixture list lands in the manifest) rather than leaving it on the normal queue — a worker slot cannot do this
      itself since `backlog.yaml` is server-side state not present in the slot's git checkout. Releasing via
      `/skip-current-task {"reason_code": "GATED"}`. — **Checked 2026-07-31T09:37Z (slot 14, ui_developer): still gated,
      no change, bare check only (per prior guidance).** Re-ran both checks via the same canonical tooling
      (`read_availability_index()` slim-column path filtered on `league_id`, not `venue` — FIXTURES rows carry league in
      `league_id`; `venue` is blank for this `data_type`) and a direct GCS parquet read of
      `latency_observations/day={2026-07-29..07-31}`: (1) FIXTURES for the 5 covered leagues — lookahead ceiling still
      `2026-08-01`, zero rows through it; last nonzero `instrument_count` row per league still in
      `2026-05-24..2026-05-29` (prior season), unchanged from the 06:18Z/08:25Z checks. (2) `stats_delayed` fires
      post-cutoff (`>2026-07-29T18:02:00Z`): **1512** total (identical count to the 08:25Z check — the underlying data
      horizon (`latency_observations` max `recorded_at_utc` = `2026-07-31T03:11:25Z`) hadn't advanced past ~6.5h before
      this check, a consolidation-cadence artifact, not a stall signal), **zero** for any of the 5 covered `league_id`s.
      This is the 3rd consecutive "still gated, no change" check since the 08:25Z entry's explicit park recommendation —
      filed `/blocked` to main reiterating it (workers can't edit `backlog.yaml` themselves, so the prose recommendation
      alone hasn't stopped re-dispatch). Releasing via `/skip-current-task {"reason_code": "GATED"}`. — **Checked
      2026-08-02T15:31Z (slot 11, backend_engineer): still gated, no change, bare check only.** Re-ran both checks via
      direct GCS parquet reads against `gs://instruments-store-sports-prd-central-element-323112/_index/`: (1)
      `availability_index.parquet` FIXTURES rows for the 5 covered leagues — lookahead ceiling still `2026-08-01`, zero
      nonzero rows through it; last nonzero `instrument_count` row per league still `2026-05-29` (prior season),
      unchanged from every prior check since 06:18Z on 2026-07-31. (2) `latency_observations` `stats_delayed` fires,
      `day={2026-07-29..2026-08-02}` (4652 total, max `recorded_at_utc=2026-08-02T15:31:40Z`): **zero** for any of the 5
      covered `league_id`s. This is now the 4th consecutive "still gated, no change" check since the first explicit park
      recommendation (08:25Z, 2026-07-31) and the task has been re-dispatched again ~2 full days later despite two prior
      `/blocked` escalations asking main/operator to park it server-side — the prose recommendation alone still hasn't
      stopped re-dispatch. Filed `/blocked` again with the same ask, flagging the now-4-day dispatch waste explicitly.
      Releasing via `/skip-current-task {"reason_code": "GATED"}`. — **Checked 2026-08-02T16:23Z (slot 3,
      data_engineering): still gated, no change, bare filtered check only (`read_availability_index(filters=...)`,
      row-group-pushdown, no full-corpus load).** FIXTURES lookahead ceiling for the 5 covered leagues still
      `2026-08-01`, zero nonzero-`instrument_count` rows through it. **Diagnosed why auto-park (RULES.md §4 /
      `auto_park.py`, threshold=3 GATED skips within a rolling 24h window) hasn't already fired despite 15+ GATED skips
      across this doc's life**: `register_cooldown`'s window resets to `skip_count=1` whenever the gap since the
      window's start exceeds `dispatch_cooldown_park_window_hours` (24h default) — and several of this task's real
      dispatch gaps (e.g. 2026-07-31T09:37Z→2026-08-02T15:31Z, ~30h) exceeded that, resetting the counter before 3
      accumulated. This is NOT a bug needing a fix — it's the mechanism correctly reflecting that dispatches have been
      sparse enough not to trip the threshold, not evidence the recommendation was ignored. Practical effect: this skip
      is #2 in the window slot-11 opened at 15:31Z; one more GATED skip before 2026-08-03T15:31Z auto-parks it without
      further operator action. Releasing via `/skip-current-task {"reason_code": "GATED"}`. — **Checked
      2026-08-02T17:31Z (slot 12, data_engineering): still gated, no change, bare filtered check only
      (`read_availability_index(columns=..., filters=[("data_type","==","FIXTURES")])` + day-partitioned
      `latency_observations` GCS reads, no full-corpus load — both run under `run-bounded-analysis.sh` per craft
      memory-bounding guardrail).** FIXTURES lookahead ceiling for the 5 covered leagues still `2026-08-01`, zero
      nonzero-`instrument_count` rows through it; last nonzero row per league still `2026-05-24..2026-05-29` (prior
      season), unchanged since every check since 2026-07-31T06:18Z. `stats_delayed` fires
      `day={2026-07-29..2026-08-02}`: 5247 total, max `recorded_at_utc=2026-08-02T17:31:44Z` (fresh/live data, not
      stalled) — **zero** for any of the 5 covered `league_id`s (top firing leagues: UECL/ROMANIA_CUP/
      ARGENTINA_PRIMERA/CZECH_REPUBLIC_CUP/BRASILEIRAO, none Understat-covered). Per the 16:23Z check's own diagnosis
      this is skip #3 in the 24h cooldown window slot-11 opened at `2026-08-02T15:31Z` — should trip `auto_park.py`'s
      threshold=3 and park this task server-side without further operator action; if it does NOT auto-park despite 3
      skips landing inside one un-reset window, that gap is itself worth a fresh diagnosis by whoever picks this up
      next. Releasing via `/skip-current-task {"reason_code": "GATED"}`. — **Checked 2026-08-03T09:45Z (slot 5, worker):
      still gated, no change, bare filtered checks only
      (`read_availability_index(columns=..., filters=[("data_type","==","FIXTURES")])` + day-partitioned
      `latency_observations` GCS reads, column-pruned, no full-corpus load).** FIXTURES rows for the 5 covered leagues:
      4261 total, 3654 nonzero-`instrument_count`, but lookahead ceiling still `2026-08-01` and the last nonzero row per
      league is still `2026-05-24..2026-05-29` (prior season) — unchanged since every check since 2026-07-31T06:18Z.
      `stats_delayed` fires `day={2026-07-29..2026-08-02}` (the 08-02 partition read partially before the scan hit its
      wall-clock bound; 08-03 not reached — the per-day parquet-file count has grown to 300-468 files/day, making a full
      6-day sweep slower than the timeout budget allotted): **6281** rows scanned across 07-29 through most of 08-02,
      **zero** for any of the 5 covered `league_id`s — consistent with every prior check's zero. Did not extend the scan
      to finish 08-02/08-03 since the FIXTURES-ceiling check already independently confirms no covered-league fixture
      exists anywhere through `2026-08-01`, and the partial stats_delayed scan already covers a large majority of the
      window with the same zero result — extending further would not change the verdict. **Process note**: per the
      16:23Z/17:31Z checks' own diagnosis, this dispatch (2026-08-03T09:45Z, ~16h14m after the 2026-08-02T15:31Z window
      open) should have been skip #4 inside that same un-reset 24h window and should already have auto-parked before
      reaching a worker at all — worth a fresh look at why `auto_park.py` hasn't tripped despite 3+ prior GATED skips
      accumulating within one window (same gap the 17:31Z check flagged, still unresolved). Releasing via
      `/skip-current-task {"reason_code": "GATED"}`. — **Checked 2026-08-06T03:15Z (slot 5, data_engineering): still
      gated, no change, bare filtered check only
      (`read_availability_index(columns=[...], filters=[("data_type","==","FIXTURES")])` + sampled
      `latency_observations` GCS reads, column-pruned, no full-corpus load).** FIXTURES rows for the 5 covered leagues:
      lookahead ceiling still `2026-08-01` (unchanged since every check since 2026-07-31T06:18Z), all 5 leagues at
      `instrument_count=0` through that date with `status=attempted_failed`. Last nonzero-`instrument_count` row per
      league still `2026-05-24..2026-05-29` (prior season), unchanged from all prior checks. `latency_observations`
      sampled across `day=2026-08-03..2026-08-06`: zero `stats_delayed` fires for any of the 5 covered `league_id`s. The
      2026-27 European season has not yet begun for BUNDESLIGA/EPL/LA_LIGA/LIGUE_1/SERIE_A. This is now ~7 days since
      the first post-fix verdict (2026-07-31T06:18Z) and the situation is structurally unchanged — the task has
      accumulated 19+ GATED skips across its lifetime. **The auto_park mechanism should have tripped after
      2026-08-02T17:31Z (skip #3 within one 24h window) per multiple prior checks' own diagnosis, yet the task continues
      to be re-dispatched ~3 days later — the `auto_park.py` gap flagged by the 17:31Z and 09:45Z checks remains
      unresolved and is now the dominant source of dispatch waste on this task.** Releasing via
      `/skip-current-task {"reason_code": "GATED"}`. — **Checked 2026-08-06 (slot 8, data_engineering): still gated, no
      change, bare filtered check only**
      (`read_availability_index(columns=[...], filters=[("data_type","==","FIXTURES")])` + day-partitioned
      `latency_observations` GCS reads, sampled 150 files/day, column-pruned, no full-corpus load, both under
      `run-bounded-analysis.sh`). FIXTURES rows for the 5 covered leagues: lookahead ceiling still `2026-08-01`, zero
      nonzero-`instrument_count` rows through it (last nonzero row per league still `2026-05-24..2026-05-29`, prior
      season) — unchanged from every check since 2026-07-31T06:18Z. `stats_delayed` fires sampled across
      `day=2026-07-30..2026-08-06` (8 partitions): 10 fires total in the sample, **zero** for any of the 5 covered
      `league_id`s. The 2026-27 European season has not yet begun for BUNDESLIGA/EPL/LA_LIGA/LIGUE_1/SERIE_A; no
      covered-league fixture exists to fire the trigger. Situation structurally unchanged. Releasing via
      `/skip-current-task {"reason_code": "GATED"}`.

## Progress Log

- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **Checked 2026-08-06 (slot 16, worker): still gated, no change, bare filtered check only (read_availability_index
  FIXTURES columns + sampled latency_observations parquet reads, column-pruned).** FIXTURES rows for the 5 covered
  leagues: lookahead ceiling still `2026-08-01`, zero nonzero-`instrument_count` rows through it; last nonzero row per
  league still `2026-05-24..2026-05-29` (prior season) — unchanged from every check since 2026-07-31T06:18Z.
  `latency_observations` sampled across `day=2026-08-03..2026-08-06`: 5 files read with pandas (no column-pruned path
  used — verified the `strings`-based grep matches were false positives from league names appearing in non-`league_id`
  fields), zero `stats_delayed` fires for any of the 5 covered `league_id`s. The 2026-27 European season has not yet
  begun for BUNDESLIGA/EPL/LA_LIGA/LIGUE_1/SERIE_A. This is now ~7 days since the first post-fix verdict
  (2026-07-31T06:18Z) with the situation structurally unchanged across 20+ checks. Releasing via
  `/skip-current-task {"reason_code": "GATED"}`.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **Checked 2026-08-09T21:00Z (slot 27, worker): still gated, no change, bare bounded check only.** (1)
  `read_availability_index(bucket, columns=[date,venue,league_id,instrument_count,status,data_type], filters=[("data_type","==","FIXTURES")])`
  for the 5 covered leagues: 4261 rows, lookahead ceiling still `2026-08-01` (unchanged since every check since
  2026-07-31), zero nonzero-`instrument_count` rows through it; last nonzero row per league still
  `2026-05-24..2026-05-29` (prior season). (2) Sampled `latency_observations` GCS parquet reads
  (`day=2026-08-06..2026-08-09`, ≤150 files/day, column-pruned to `trigger_name`/`league_id`/`recorded_at_utc`, run
  under `run-bounded-analysis.sh`): 568 `stats_delayed` rows scanned, max `recorded_at_utc=2026-08-09T20:51:07Z`
  (fresh/live, not stalled) — **zero** for any of the 5 Understat-covered `league_id`s. The 2026-27 European season has
  still not begun for BUNDESLIGA/EPL/LA_LIGA/LIGUE_1/SERIE_A; this is now ~9 days since the first post-fix verdict
  (2026-07-31T06:18Z), structurally unchanged across 21+ checks. No code change indicated — this remains a
  season-schedule gate, not a pipeline defect. Releasing via
  `/skip-current-task {"reason_code": "GATED", "estimated_unblock_minutes": 180}` (cap per RULES.md § 4c); the prior
  checks' repeated asks to park this server-side (`priority: 999` + `priority_override: true` + a
  `sports-understat-season-active`-style prerequisite) still stand — a worker cannot edit `data/config/backlog.yaml`
  from this slot's checkout (confirmed absent from every slot repo).
- **Checked 2026-08-10T01:06Z (slot 6, ui_developer): still gated, no change — but this check used the CORRECT live
  data_type for the first time, giving a stronger confirmation than the prior 22.** Before re-running the standard
  checks, verified the doc's own methodology: every prior check queried `data_type=="FIXTURES"` for the lookahead
  ceiling. Confirmed via `read_availability_index_safe` that `FIXTURES` is a LEGACY data_type frozen at max
  `date=2026-08-01` since ~2026-07-24 — it has not advanced in 2+ weeks even as real time passed it. The actual live
  data_type is `FIXTURES_SCHEDULE` (written by `instruments_service/triggers/sports_fixtures_daily_repoll.py`, Phase B.1
  of `instruments_master.md` — a rolling `[today-1d, today+8d]` window), which correctly shows fresh rows through
  `2026-08-16` (today+6d, consistent with the rolling window still running). Re-ran the lookahead-ceiling check against
  `FIXTURES_SCHEDULE` for the 5 covered leagues: **same zero-nonzero-past-2026-05-29 result** as every prior `FIXTURES`
  check — this INDEPENDENTLY confirms the off-season verdict is correct (not an artifact of querying a stale/frozen
  data_type) and rules out my initial hypothesis that the whole 22-check history might have been reading dead data.
  Updated the todo's own "Also note" guidance above to point future checks at `FIXTURES_SCHEDULE` instead of `FIXTURES`
  so this doesn't have to be re-discovered. Also sampled `latency_observations` `day=2026-08-07..2026-08-10` (≤150
  files/day, column-pruned): 1152 `stats_delayed` rows, max `recorded_at_utc=2026-08-10T01:06:12Z` (fresh/live),
  **zero** for any of the 5 covered `league_id`s. Situation structurally unchanged, now confirmed via the live
  data_type; this is ~10 days since the first post-fix verdict (2026-07-31T06:18Z), 23+ checks. Releasing via
  `/skip-current-task {"reason_code": "GATED", "estimated_unblock_minutes": 180}`; the standing ask to park this
  server-side (`priority: 999` + `priority_override: true` + a season-active prerequisite) still stands and remains
  outside a worker slot's reach.
- **Checked 2026-08-10T05:14Z (slot 10, infra): still gated, no change, bare filtered check only
  (`read_availability_index(bucket, columns=[date,venue,league_id,instrument_count,status,data_type], filters=[("data_type","==","FIXTURES_SCHEDULE")])`
  - sampled `latency_observations` GCS parquet reads, column-pruned, both under `run-bounded-analysis.sh`).** (1)
    `FIXTURES_SCHEDULE` for the 5 covered leagues: 20691 rows, window now runs `2018-01-01..2026-08-17` (rolling ceiling
    advanced 1 day past the 01:06Z check's `2026-08-16`, as expected); 9845 nonzero-`instrument_count` rows but the max
    `date` per league is still `2026-05-24..2026-05-29` (prior season) — unchanged since every check since 2026-07-31.
    (2) `latency_observations` `day=2026-08-08..2026-08-10` (≤150 files/day, column-pruned to
    `trigger_name`/`league_id`/`recorded_at_utc`): 1152 `stats_delayed` rows, max `recorded_at_utc=2026-08-10T04:11:06Z`
    (fresh/live, not stalled) — **zero** for any of the 5 Understat-covered `league_id`s. The 2026-27 European season
    has still not begun for BUNDESLIGA/EPL/LA_LIGA/LIGUE_1/SERIE_A; ~10.5 days since the first post-fix verdict
    (2026-07-31T06:18Z), 25+ checks with the identical result. No code change indicated — this remains a season-schedule
    gate, not a pipeline defect. Releasing via
    `/skip-current-task {"reason_code": "GATED", "estimated_unblock_minutes": 180}` (cap per RULES.md § 4c); reiterating
    the long-standing ask to park this task server-side (`priority: 999` + `priority_override: true` + a
    `sports-understat-season-active`-style prerequisite, RULES.md § 4 "Park a task") — this is now the 3rd+
    separately-authored check flagging that the auto-park mechanism has still not fired despite 25+ GATED skips across
    this doc's ~10-day life; still outside a worker slot's reach to fix directly (`data/config/backlog.yaml` is
    server-side state, absent from every slot checkout).
- **Checked 2026-08-10 (slot 17, worker): BREAKTHROUGH — LA_LIGA 2026-27 season fixtures are now in the manifest, but
  still gated (no fires yet).** (1) `FIXTURES_SCHEDULE` (`pd.read_parquet` directly from GCS, column-pruned to
  `date`/`league_id`/`instrument_count`/`capture_status`/`data_type`): LA_LIGA has **3 nonzero-`instrument_count` rows**
  from Aug 1 onward — `2026-08-15` (count=2), `2026-08-16` (count=3), `2026-08-17` (count=1), all `status=captured`.
  This is the FIRST check (of 26+) where ANY covered league shows nonzero fixtures — all prior checks found zero across
  all 5. BUNDESLIGA/EPL/LIGUE_1/SERIE_A still zero from Aug 1 (off-season). Non-covered leagues' max nonzero date is
  `2026-12-06` (manifest rolling window healthy). (2) `latency_observations` `day=2026-08-01..2026-08-10` (column-pruned
  to `trigger_name`/`league_id`): **zero** `stats_delayed` fires for LA_LIGA or any other covered league across the full
  10-day window (888-3414 fires/day, all non-covered leagues). Fixtures are scheduled but haven't kicked off yet —
  `stats_delayed` fires at kickoff+25.25h..26.25h, so the earliest possible fire for the Aug 15 fixture is ~Aug 16
  mid-day UTC. **Concrete next step**: re-check no earlier than `2026-08-17` (~7 days) — by then the Aug 15 fixture will
  have kicked off and its `stats_delayed` window will have passed, giving the first real opportunity for end-to-end
  verification. This is no longer an indefinite off-season wait — the season IS starting, with a specific date.
  Releasing via `/skip-current-task {"reason_code": "GATED", "estimated_unblock_minutes": 180}` (cap per RULES.md § 4c).
  Reiterating the standing park recommendation, now with a concrete unblock date (`sports-understat-season-active`
  prerequisite flipped `true` ~Aug 17).
- **Checked 2026-08-11 (slot 30, data_engineering): still gated, no change, bare filtered check only
  (`read_availability_index(columns=[...], filters=[("data_type","==","FIXTURES_SCHEDULE")])` + sampled
  `latency_observations` via `StorageClient.list_blobs()`, column-pruned, no full-corpus load).** (1)
  `FIXTURES_SCHEDULE` for the 5 covered leagues: LA_LIGA unchanged at 3 nonzero rows Aug 15-17 (count=2/3/1, all
  `captured`); BUNDESLIGA/EPL/LIGUE_1/SERIE_A still zero from Aug 1 (off-season). Rolling ceiling unchanged at
  `2026-08-17`. (2) `latency_observations` `day=2026-08-08..2026-08-11` (≤150 files/day, column-pruned to
  `trigger_name`/`league_id`/`recorded_at_utc`): 1360 `stats_delayed` rows, max `recorded_at_utc=2026-08-11T01:31Z`
  (fresh/live, not stalled) — **zero** for any of the 5 Understat-covered `league_id`s. No change from the slot-17 check
  ~1 day ago. The first LA_LIGA fixture is still Aug 15; earliest possible `stats_delayed` fire is ~Aug 16 mid-day UTC
  (~5 days from now). Releasing via `/skip-current-task {"reason_code": "GATED", "estimated_unblock_minutes": 180}` (cap
  per RULES.md § 4c). Reiterating the standing park recommendation — the concrete unblock date (~Aug 17) from the
  slot-17 check still holds.
