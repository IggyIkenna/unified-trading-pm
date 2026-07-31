---
doc_type: issue
title:
  "instruments-service CLI --venues arg is stored lowercase (never uppercased) — a lowercase --venues api_football
  invocation case-mismatches the UAC VENUE_TO_ADAPTER_KEY registry lookup, false-marking API_FOOTBALL as having no URDI
  adapter and stamping every zero-fixture league that date as attempted_failed(FIXTURES_FETCH_FAILED) instead of honest
  empty_confirmed(EXPECTED_NO_FIXTURE)"
summary:
  "data_engineering (slot-3, 2026-07-31) hit this while executing sports_satellite_ao_dispatch_batch8-006 (junk-symbol
  guard corpus-loss recapture), running the exact --venues api_football invocation the plan itself quotes. Every date
  processed (2021-11-20 through at least 2021-11-23, 4/4 so far) logged an identical 'SPORTS: fixtures FETCH FAILED for
  date=<date> — wrote attempted_failed markers for 383 leagues' warning plus a 'No URDI adapter for 1 venue(s) ...
  api_football' warning. Traced end-to-end: instruments_service/cli/instruments_handler.py:174-176 stores
  self._venue_override = venues_arg VERBATIM (no .upper()), unlike sports_provider_arg.upper() two lines below at line
  187 which DOES normalize. The lowercase 'api_football' then flows through process_instruments ->
  _resolve_venues_and_preflight -> fetch_instruments_for_all_venues ->
  instruments_service/engine/urdi_reference_provider.py:101 VENUE_TO_ADAPTER_KEY.get('api_football') (case-sensitive
  dict lookup) against the UPPERCASE-keyed
  unified-api-contracts/unified_api_contracts/registry/venue_adapter_keys.py:216 entry 'API_FOOTBALL': 'api_football' —
  the lowercase lookup misses, API_FOOTBALL is marked unsupported/failed, so it is excluded from non_error_venues, and
  instruments_service/engine/orchestrator/process.py's _fixtures_fetch_failed() (the same function whose docstring cites
  a prior 2026-07-13 root-cause fix for a related false-positive class) returns True for every date. The REAL sports
  fixture data capture is unaffected (a separate bespoke code path successfully wrote 1329/1119 real canonical fixtures
  per date in this same run) — only the zero-fixture-league bookkeeping in process_zero_records.py is mis-stamped."
status: resolved
priority: P1
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [manifest, case-sensitivity, venue-override, attempted_failed, false-positive, data-correctness, sports]
related: [/plans/active/sports_satellite_ao_dispatch_batch8_2026_07_30.md]
created: 2026-07-31
parent_epic: sports_master
source:
  "data_engineering worker (slot-3, planning VM), 2026-07-31, executing AO task sports_satellite_ao_dispatch_batch8-006
  (junk-symbol-guard corpus-loss recapture). Observed live against instruments-store-sports-prd-central-element-323112
  while running: GCP_PROJECT_ID=central-element-323112 instruments-service --operation instruments --mode batch
  --asset-group sports --venues api_football --start-date 2021-11-20 --end-date 2021-12-02 --force (the exact lowercase
  venue form the plan's own prior attempt quoted). Identical 'wrote attempted_failed markers for 383 leagues' + 'No URDI
  adapter for 1 venue(s) ... api_football' warning pair fired on every date processed (2021-11-20, -21, -22, -23)."
locked_by:
resolved_by: instruments-service@627fd31c
execution_scope: orchestrator-agent
assigned_role: backend_engineer
model_tier: sonnet-doable
drift_direction: advance-code
assigned_vm: planning
depends_on: []
last_updated: 2026-07-31
---

## What I found

`instruments_service/cli/instruments_handler.py::_wire_cli_filters_from_args` (lines ~171-176):

```python
venues_arg: list[str] | None = getattr(self.args, "venues", None) if self.args else None
if venues_arg:
    self._venue_override = venues_arg
    logger.info("Venue override from CLI: %s", venues_arg)
```

stores the raw `--venues` CLI value **verbatim, case-preserved** — unlike `sports_provider_arg.upper()` two lines
further down (line ~187) in the same method, which DOES normalize its own CLI arg. `self._venue_override` flows straight
through `process_instruments(venue_override=self._venue_override, ...)` into the venue-resolution /ected fetch path,
ultimately reaching `instruments_service/engine/urdi_reference_provider.py:101`:

```python
adapter_key = VENUE_TO_ADAPTER_KEY.get(canonical)
if adapter_key is None or adapter_key == NO_ADAPTER_YET:
    unsupported.append(canonical)
```

`VENUE_TO_ADAPTER_KEY` (`unified-api-contracts/unified_api_contracts/registry/venue_adapter_keys.py:216`) is keyed
**uppercase**: `"API_FOOTBALL": "api_football"`. A lowercase `canonical` (`"api_football"`) misses the dict lookup
entirely (`.get()` returns `None`), so the venue is classified `unsupported` and logged:
`"No URDI adapter for 1 venue(s) ... ['api_football']"` — even though the venue genuinely IS registered, just under a
different case.

That "unsupported" classification propagates into `non_defi_result.failed_venues` → `process_fetch.py`'s
`_non_error_venues` never gets `'api_football'` (or `'API_FOOTBALL'`) added → back in
`process.py::_fixtures_fetch_failed()`, `_checkable_venues = ['api_football']` (or whatever case was passed) is not a
subset of `non_error_venues`, so the function returns `True` for **every date** in the run, regardless of whether the
day's real fixture fetch actually succeeded.

`process_zero_records.py` then treats every league with zero fixtures that day as a **genuine fetch failure**
(`FIXTURES_FETCH_FAILED`) rather than honest absence (`EXPECTED_NO_FIXTURE`):

```python
if fixtures_fetch_failed:
    _empty_manifest.record_failed(row_key=_row_key, error="FIXTURES_FETCH_FAILED", ...)
```

**Confirmed NOT a data-loss bug** — the real sports fixture capture (the data the junk-symbol-guard fix and this AO
task's own recapture depend on) runs through a separate, bespoke sports-orchestrator dispatch (`sports_fixtures.py` /
`sports_reference_core.py`), not through this generic URDI adapter-key path, and it succeeded normally in the same run
(`"Canonical fixtures fetched from API and written to entity=fixtures/ (1329 fixtures)"` for 2021-11-20, `1119` for
2021-11-22, etc.). This is a **manifest bookkeeping/capture_status correctness bug**, not a fixture-loss bug: the
zero-fixture leagues for the affected dates are stamped with the wrong `capture_status` (`attempted_failed` instead of
`empty_confirmed`), which pollutes attempted-failed counts/dashboards and could mask genuinely failed leagues among the
noise.

**Reproduced identically on 7/7 dates** processed in the (killed) first attempt of this session's recapture run
(2021-11-20 through 2021-11-26), each logging the exact same `"wrote attempted_failed markers for 383 leagues"` count
alongside the `"No URDI adapter"` warning for `api_football`.

**UPGRADED 2026-07-31 (P2 → P1) — this also silently no-ops `instrument_availability` writes + the junk-symbol guard
itself, not just manifest bookkeeping.** Re-reading the full flow: when the generic URDI fetch classifies `api_football`
(lowercase) as `unsupported`, `fetch_instruments_for_all_venues` returns **zero records** for that venue — meaning
`process_fetch.py::_filter_and_enrich_records` (the ONLY call site of `reject_junk_instruments`, i.e. the junk-symbol
guard this session's own AO task, `sports_satellite_ao_dispatch_batch8-006`, exists to validate) receives an EMPTY list
and the guard never runs at all on real data. This is DISTINCT from the separate bespoke
`sports_reference_fixtures.py::_ensure_canonical_fixtures` path (the
`"Canonical fixtures fetched from API and written to entity=fixtures/"` line) — that path writes directly to
`sports_reference/by_date/day={date}/.../entity=fixtures/` via `_write_fixtures_per_league`, completely bypassing
`reject_junk_instruments`; it was never gated by the guard in the first place, on ANY casing. So a
`--venues api_football` (lowercase) invocation of `--operation instruments` for sports:

1. Never writes (or refreshes) `instrument_availability/by_date/day={date}/venue=API_FOOTBALL/instruments.parquet` for
   that date (the URDI-fetch stage that feeds this write gets 0 records for the venue).
2. Never exercises the junk-symbol guard (`reject_junk_instruments`) against real sports data at all, on any casing of
   the venue name being what production actually calls with — only an `API_FOOTBALL`-cased (or no `--venues` override,
   since the default venue list in `venue_core.py::get_venues_for_asset_groups` is hardcoded uppercase) invocation
   exercises it.
3. Mis-stamps the 383 zero-fixture leagues that date as `attempted_failed` (the original finding).

This session had to kill and restart its own recapture (`--venues api_football` → `--venues API_FOOTBALL`) after
discovering 0 junk-guard-rejection log lines were a false negative caused by this bug, not evidence the fix works.

## Why it matters

- Every `instruments-service --operation instruments ... --venues api_football` invocation using **lowercase**
  `api_football` (exactly the form quoted in this task's own source plan,
  `plans/active/sports_satellite_ao_dispatch_batch8_2026_07_30.md` line 173) silently mis-stamps a large batch of
  manifest rows (383 leagues/day observed) as `attempted_failed` instead of honest `empty_confirmed`, corpus-wide, for
  as long as this bug has existed.
- This corrupts `capture_status` accuracy for the sports `FIXTURES_SCHEDULE` data_type specifically — coverage/failure
  dashboards, the `/data-freshness` skill, and any downstream consumer reading `attempted_failed` counts for sports will
  over-report failures for dates run with a lowercase venue override.
- **Bigger than manifest bookkeeping (2026-07-31 upgrade)**: a lowercase `--venues api_football` invocation also
  silently no-ops the `instrument_availability/by_date/day={date}/venue=API_FOOTBALL/instruments.parquet` write for that
  date/venue AND never exercises the junk-symbol guard (`reject_junk_instruments`) against real data — the guard is the
  ONE thing `sports_satellite_ao_dispatch_batch8-006` (this issue's own source task) exists to validate. Any attempt to
  measure or trust that guard's behavior via a lowercase-venue CLI run produces a false "0 rejected" negative, not a
  real result.
- **Production-impact uncertainty (flagging honestly, not fixing myself)**: I did NOT verify whether the live/cron/
  scheduled sports pipelines pass `--venues API_FOOTBALL` (uppercase, unaffected) or `api_football` (lowercase,
  affected) — this matters for priority. If production automation always uses canonical uppercase venue names, the
  live/blast radius is limited to manual/interactive invocations (like this one, and like the plan's own prior attempt).
  If any scheduled job passes lowercase, this has been silently mis-stamping manifest rows in production. **This check
  should be the fix-todo's first step**, before or alongside the code fix.

## Recommended decision

Fix is small and precisely located — mirror the existing `sports_provider_arg.upper()` normalization pattern already
used two lines below in the same method:

```python
# instruments_service/cli/instruments_handler.py, in _wire_cli_filters_from_args()
if venues_arg:
    self._venue_override = [v.upper() for v in venues_arg]
    logger.info("Venue override from CLI: %s", self._venue_override)
```

Add a regression test pinning that `--venues api_football` (lowercase CLI input) resolves to
`self._venue_override == ["API_FOOTBALL"]`, and that `_fixtures_fetch_failed()` returns `False` for a day where the real
fetch succeeded regardless of the CLI venue-arg casing. Also worth a quick grep for other CLI arg fields threaded into
UAC-keyed registry lookups without normalization (the `sports_provider_arg.upper()` precedent suggests this was known to
matter for at least one field but missed for `venues`).

- [x] ✅ [CODE] P1. **DONE 2026-07-31 (slot-14, backend_engineer)** — `instruments-service@627fd31c`. First check
      whether any live/cron/scheduled sports pipeline invocation passes `--venues` in lowercase (grep launcher scripts +
      `agent-orchestrator`/cron configs for `--venues api_football` or similar lowercase forms) to establish real
      production blast radius, then fix `instruments_service/cli/instruments_handler.py::_wire_cli_filters_from_args` to
      uppercase `venues_arg` before storing it in `self._venue_override` (mirror the existing
      `sports_provider_arg.upper()` pattern two lines below), add a regression test per the "Recommended decision"
      section above, and re-run a small `--force` recapture over a day or two known to have zero-fixture leagues to
      confirm (a) `instrument_availability/.../venue=API_FOOTBALL/     instruments.parquet` is actually
      written/refreshed and (b) the `attempted_failed` markers correctly flip to `empty_confirmed`. (repo:
      instruments-service)

      **Blast-radius check**: grepped every `*.sh`/`*.py`/`*.yml`/`*.yaml` launcher/cron/scheduler across the
                  canonical repo checkouts (deployment-service `scripts/vm/`, `terraform/gcp/sports_scheduler_cron.tf`,
                  `deployment_service/sports_trigger_*.py`, agent-orchestrator configs) for a lowercase `--venues api_football`
                  invocation — zero hits outside doc/plan prose. The one VM launcher that sets `--venues`
                  (`deployment-service/scripts/vm/vm_instruments_reference.sh:36`) defaults `VENUES="API_FOOTBALL"` (uppercase);
                  the live Cloud Scheduler dispatch path (`sports_trigger_periodic.py`/`sports_trigger_scheduler.py`) never passes
                  `--venues` at all — it uses the hardcoded-uppercase default list in `venue_core.py::get_venues_for_asset_groups`.
                  **Blast radius confirmed limited to manual/interactive invocations** (the plan's own quoted example and the
                  original bug-reporting worker's run) — no production automation was affected.

                  **Fix**: `instruments_service/cli/instruments_handler.py::_wire_cli_filters_from_args` now stores
                  `self._venue_override = [v.upper() for v in venues_arg]` (mirrors `sports_provider_arg.upper()` two lines below)
                  and threads the normalised list into `earliest_venue_date()` too (that lookup is keyed the same
                  UAC-uppercase way, so it was equally exposed). Checked `_sports_entity_filter`/`_trigger_name` (the other two
                  unnormalized CLI-arg fields in the same method) — both are opaque filter strings, not UAC-registry dict keys, so
                  out of scope for this bug class.

                  **Regression test**: `tests/unit/test_cli_handler_boost.py::test_wire_cli_filters_venues_uppercased_regardless_of_cli_casing`
                  pins `--venues api_football` (lowercase CLI input) → `handler._venue_override == ["API_FOOTBALL"]` +
                  `earliest_venue_date` called with the normalised list. All 4 `wire_cli_filters` tests pass.

                  **Verification recapture** (`GCP_PROJECT_ID=central-element-323112 instruments-service --operation instruments
                  --mode batch --asset-group sports --venues api_football --start-date 2021-11-20 --end-date 2021-11-20 --force`,
                  the exact lowercase invocation the original bug report used): full run log (4984 lines) shows **zero** `"No URDI
                  adapter"` warnings and **zero** `"wrote attempted_failed markers"` lines (both fired on every date pre-fix);
                  `"Venue override from CLI: ['API_FOOTBALL']"` confirms normalisation. Confirmed both done-criteria: (a)
                  `gsutil ls gs://instruments-store-sports-prd-central-element-323112/instrument_availability/by_date/day=2021-11-20/venue=API_FOOTBALL/`
                  shows `instruments.parquet` written; (b) `ManifestWriter: updated availability index (11812025 total entries,
                  2107 new)` + `Shard completeness OK: 8/1 venues written for date=2021-11-20` + `instruments: date=2021-11-20 wrote
                  43682 records across 359 venues` — the zero-fixture-league false-failure path never fired. quality-gates.sh: full
                  run PASSED (90s) with sentinel written at `627fd31c`; the run's overall exit code was non-zero only due to an
                  UNRELATED, pre-existing cross-repo check (`deployment-api/deployment_api/services/data_status/mtds.py` adapter-
                  contract baseline drift from an already-merged decompose refactor, tracked separately at
                  `deployment_api_qg_size_gate_debt_2026_07_30.md`) — verified zero overlap with this task's diff. Shipped via
                  quickmerge --agent (sentinel-verified fast path).
