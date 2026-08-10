---
doc_type: issue
title:
  a sports_reference entity=fixtures object under instruments-store-sports-prd contains instrument-catalog schema
  content instead of api-football fixture data
summary: >-
  While running the peripheral-bucket league-vocabulary migration
  (issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md), the cross-entity resolver's parquet
  read of an entity=fixtures object failed with a schema mismatch, not a missing-column error. Direct verification
  confirmed the object genuinely exists at
  sports_reference/by_date/day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures/league=BOLIVIA_PRIMERA_DIVISION/fixtures.parquet
  in instruments-store-sports-prd-central-element-323112, and its content is an INSTRUMENT-CATALOG schema
  (instrument_key, venue, instrument_type, raw_symbol, base_asset, quote_asset, asset_class, tick_size, contract_size,
  expiry, strike, option_type, underlying, margin_type, is_trading_day, trading-session timestamps, holiday_calendar,
  timezone, __fragment_index/__batch_index/__filename) — not api-football sports fixture data (af_league_id, teams,
  kickoff time, etc.). The same "No match for FieldRef.Name(af_league_id) in <schema>" error pattern recurred
  identically across 54 distinct league values during the 2026-08-09 dry-run census of this bucket (see the sibling
  issue's Progress Log), suggesting this is not an isolated one-object accident.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [sports, data-correctness, schema-contamination, gcs, instruments-store-sports-prd]
related:
  [
    /plans/active/issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md,
    /plans/archive/2026_07/sports_closeout_track_x_hygiene_2026_07_25.md,
  ]
created: "2026-08-09"
author: sports_closeout_track_x_hygiene-006 (slot-6, data_engineering)
source: >-
  Discovered mid-migration while running the league-vocabulary resolver's cross-entity fixtures lookup for
  sports_closeout_track_x_hygiene-006's migration dispatch, 2026-08-09.
resolved_by:
locked_by:
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md,
    /codex/02-data/sports-gcs-path-ssot.md,
    /codex/05-infrastructure/gcs-object-operations.md,
  ]
---

# Sports fixtures object carries instrument-catalog schema, not fixture data

## What was found (2026-08-09, mid-migration)

Running the league-vocabulary migration's cross-entity resolver (`_resolve_canonical_league()` in
`market-tick-data-service/scripts/sports/league_id_relocation/migrate_instruments_store_sports_league_vocabulary_2026_08_04.py`)
against `instruments-store-sports-prd-central-element-323112`, a `pd.read_parquet(..., columns=["af_league_id"])` call
raised:

```
No match for FieldRef.Name(af_league_id) in instrument_key: string
venue: string
instrument_type: string
raw_symbol: string
base_asset: string
quote_asset: string
status: string
available_from_datetime: timestamp[us, tz=UTC]
available_to_datetime: timestamp[us, tz=UTC]
asset_class: string
settle_asset: null
tick_size: decimal128(2, 2)
min_size: decimal128(1, 0)
contract_size: decimal128(1, 0)
expiry: timestamp[us, tz=UTC]
strike: null
option_type: null
underlying: null
margin_type: null
legs: null
is_trading_day: null
regular_open_utc: null
regular_close_utc: null
early_close_utc: null
pre_market_open_utc: null
post_market_close_utc: null
auction_open_utc: null
auction_close_utc: null
holiday_calendar: null
timezone: string
available_at: timestamp[us, tz=UTC]
__fragment_index: int32
__batch_index: int32
__last_in_fragment: bool
__filename: string
```

This is an `InstrumentRecord`-shaped schema (venue/instrument_type/base_asset/quote_asset/tick_size/contract_size/
expiry/strike/option_type/margin_type/trading-session-times/holiday_calendar) — the shape instruments-service uses for
its general instrument-universe catalog, NOT api-football sports fixture data.

**Direct verification** (bypassing the migration script, downloading the object directly via
`unified_trading_library.download_from_storage`):

- Path:
  `sports_reference/by_date/day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures/league=BOLIVIA_PRIMERA_DIVISION/fixtures.parquet`
- Bucket: `instruments-store-sports-prd-central-element-323112`
- The object genuinely EXISTS (not a 404 masked as something else) and is 8,194 bytes of valid parquet with the
  instrument-catalog schema above. `download_from_storage()` itself is NOT at fault here — it returned the real bytes at
  that path; those bytes are simply the wrong content type for the path they live at.
- Only 3 objects total exist under this exact `(day, pipeline_mode, league)` triple, which is why this wasn't previously
  caught by spot checks.

**Not isolated**: the same `"No match for FieldRef.Name(af_league_id)"` error pattern recurred for 54 distinct league
values during the 2026-08-09 full-bucket dry-run census (out of 450 non-numeric quarantined values) — see
`issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md`'s 2026-08-09 Progress Log entry for the
full list of affected league values. Each occurrence was a small object count (single digits to low tens), consistent
with a rare/edge-case write-path bug rather than a bulk corruption.

## Why this is filed separately

This is a DIFFERENT correctness problem from the league-vocabulary-contamination issue that surfaced it: that issue is
about the wrong VALUE in the `league=` path segment; this is about the wrong CONTENT TYPE inside the object entirely
(sports fixture path, instrument-catalog payload). Fixing the vocabulary contamination does not touch this — these
objects need their own root-cause trace and remediation (most likely: quarantine/re-fetch, not a path rename, since the
content itself is wrong, not just misfiled).

## Required work (not started)

1. **Confirm scope**: enumerate every object across `instruments-store-sports-prd` (and check `features-sports-prd` too,
   given the sibling issue's finding that the SAME normalizer feeds both buckets) whose parquet schema does not match
   the expected schema for its `entity=` partition. A per-entity expected-schema check (not just `entity=fixtures`) is
   the right scope — this instance happened to be caught via the fixtures-specific `af_league_id` read, but the same
   failure mode could affect other entities silently.
2. **Root-cause**: identify the writer that produced `day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures`
   content shaped like instruments-service's `InstrumentRecord` catalog. Candidates to check: a shared serialization
   helper reused across both instrument-catalog and sports-fixture write paths that picked the wrong schema/template for
   this call; a path-construction bug that wrote instrument-catalog output to a sports-shaped path; or a cross-service
   GCS client misconfiguration (bucket/prefix mixup) on 2026-04-14 specifically.
3. **Remediate**: once root-caused, decide fix-at-write-path (if live) and whether the specific mis-shaped objects
   should be re-fetched from api-football (if recoverable) or quarantined/deleted per the delete-safety protocol (if
   not).

P1 because it is a **content-correctness** bug (wrong schema entirely, not just wrong path/value) that could silently
break any downstream reader assuming `entity=fixtures` always carries fixture columns — worse than the vocabulary
contamination this issue was found alongside.

Evidence: `sports_closeout_track_x_hygiene-006` dispatch session (slot-6, 2026-08-09) — direct GCS verification
transcript available in that session's Progress Log entry on
`plans/archive/2026_07/sports_closeout_track_x_hygiene_2026_07_25.md`.

## Todos

- [x] ✅ [DATA] P1. Enumerate the full scope of schema-mismatched objects across `features-sports-prd` (all
      `feature_group=` partitions). **RESOLVED (2026-08-10, slot-29)** — census VM
      `sports-schema-census-features-sports-20260809-225453` terminated cleanly (`EXIT_STATUS=0`, `run.log`:
      `DONE: validated=158826 total_rows_in_report=158826`). Downloaded + analyzed the 158,826-row report directly:
      `contamination_codes` non-empty on **0** rows across every `feature_group`
      (`fixture_features`/`derived_features`/`fixtures`/`standings`/`teams`/`venues`/
      `fixture_events`/`leagues`/`sfi_progressive`/`odds_features`/`fixture_lineups`/`fixture_stats`/
      `injuries`/`odds_targets`/`fixture_player_stats`), 0 `READ_ERROR` rows. **`features-sports-prd` carries zero
      schema-mismatched objects.** (repo: instruments-service — split off the original combined todo below; see Progress
      Log for full detail — instruments-service/unified-trading-pm)
- [ ] [DATA] P1. Enumerate the full scope of schema-mismatched objects across `instruments-store-sports-prd` (all
      `entity=` partitions, not just `fixtures`). Produce a per-entity, per-schema-shape count. This is corpus-scale
      (the sibling issue already flagged `instruments-store-sports-prd` as needing a dedicated bounded VM walk for a
      full census) — run as a bounded VM job, not an interactive dispatch. **STATUS (2026-08-10, slot-29)**: census VM
      `sports-schema-census-instruments-store-20260809-224053` confirmed still `RUNNING` (not self-deleted), 333,000
      rows checkpointed as of this check, 0 contamination hits so far in the `day` range covered
      (`2019-01-01`–`2021-07-18`, 410 distinct days) — healthy, no stall, but genuinely many more hours of corpus remain
      at the observed pace (the one known-contaminated object is at `day=2026-04-14`, ~4.5 years past the current
      frontier). (repo: instruments-service / market-tick-data-service). **Done when**: a report exists listing every
      object whose parquet schema does not match its `entity=` partition's expected schema, with counts by
      entity/day/pipeline_mode — the walk must reach `NOT_FOUND` on `gcloud compute instances describe` (genuine
      terminal self-delete) before trusting any "complete"-looking log line (see the false-SUCCEEDED lesson in the
      Progress Log above).
- [x] ✅ [DATA] P1. Root-cause the writer that produced the
      `day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures/league=BOLIVIA_PRIMERA_DIVISION/fixtures.parquet`
      instrument-catalog-shaped object. **RESOLVED (2026-08-09, slot-15)** — see the Progress Log entry below for full
      evidence: this is the SAME already-documented-and-fixed incident as
      `/plans/active/issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`'s 85 `entity=fixtures_schedule`
      objects (identical burst-write timestamp window, size class, content-type), not a new/separate bug. The exact
      historical calling script is unrecoverable (same GCS Data Access audit-logging gap that doc's own DIAG todo hit),
      but the structural mechanism is fully understood and the fix already shipped (`instruments-service@b3cb6f8c`)
      structurally covers this entity too — see evidence below.
- [ ] [DATA] P1. Fix the write path (if still live) and remediate the existing mis-shaped objects (re-fetch if
      recoverable, else quarantine/delete per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`), gated on the
      two todos above. (repo: instruments-service / market-tick-data-service). **Done when**: a fresh scoped check of
      the affected (day, pipeline_mode, entity) triples returns 0 schema-mismatched objects.
- [x] ✅ [SCRIPT] P2. `deployment-service/scripts/vm/lib/launcher_common.sh`'s `lc_verify_setup_script_freshness()`
      defaults to `LC_SETUP_SCRIPT_FRESHNESS=warn`, which lets a Pattern-A VM boot and fetch a stale GCS-published
      `setup-data-pipeline-vm.sh` even when the fix already landed in git — the exact race that hit this issue's own
      relaunch #1 (`sports-schema-census-instruments-store-20260809-222731`, same
      `VM_TASK=sports-schema-census has no dedicated dispatch branch` error recurring after the dispatch-branch fix was
      already shipped and pushed). Same failure class as the prior-documented incident
      `defi_morpho_lending_indices_never_wired_2026_07_12.md`. Discovered 2026-08-09 (slot-16) — worked around this
      session by passing `LC_SETUP_SCRIPT_FRESHNESS=enforce` explicitly on relaunch. (repo: deployment-service). **Done
      when**: either the default mode is reconsidered (`warn`→`enforce` or `auto`) with the tradeoffs documented, or
      every fix-then-relaunch call site across `scripts/vm/launch-*.sh` is audited for whether it should pass
      `LC_SETUP_SCRIPT_FRESHNESS=enforce` explicitly rather than relying on the silent-warn default. **RESOLVED
      (2026-08-09, slot-15)** — `deployment-service@7407554a` reconsidered the default to `auto`, see the Progress Log
      entry below.

## Progress Log

- **2026-08-09 (slot-6, data_engineering, discovered during `sports_closeout_track_x_hygiene-006`)**: filed this issue
  after direct GCS verification confirmed the anomaly is real (not a script bug) — see "What was found" above for the
  full transcript. Did not investigate root cause or remediate; out of scope for the migration task that surfaced it.
- **2026-08-09 (slot-15, data_engineering)**: root-caused the DATA P1 todo above.

  **Evidence-gap note first**: this issue's own text cites "the 53 other affected league values found the same day's
  census — see the sibling issue's 2026-08-09 Progress Log for the full list." Checked both places that citation could
  resolve to — `/plans/active/issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md` (the linked
  sibling issue) and `/plans/archive/2026_07/sports_closeout_track_x_hygiene_2026_07_25.md` (the dispatch session named
  in this doc's own "Evidence" line) — neither contains a 2026-08-09 entry with a 53/54-league list or any
  `af_league_id`/schema-mismatch content. The census this doc's "Not isolated" paragraph describes may have run in a
  session that never got committed, or the citation is simply wrong. Proceeded on the one item this doc DOES verify
  directly (the BOLIVIA_PRIMERA_DIVISION object) rather than blocking on the missing list — that's todo 1's scope
  (full-corpus enumeration, dispatched separately to slot 16) to re-derive properly via a bounded VM walk, not this
  todo's.

  **Root cause — direct evidence chain**:
  1. Described the confirmed object directly (`gcs_describe_object`, one bounded call, no corpus walk):
     `gs://instruments-store-sports-prd-central-element-323112/sports_reference/by_date/day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures/league=BOLIVIA_PRIMERA_DIVISION/fixtures.parquet`
     → `size=8194`, `last_modified=2026-07-16T09:59:20.685Z`, `content_type=application/octet-stream`.
  2. That timestamp falls **inside** the exact `2026-07-16T09:59:21.462Z–09:59:22.039Z` sub-2-second burst window
     already root-caused in `/plans/active/issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md` (slot 12's
     2026-07-24 GCS-metadata finding) for the 85 `entity=fixtures_schedule` contaminated objects on the SAME
     `day=2026-04-14` partition — this object lands ~0.8s before that window starts, consistent with one script writing
     multiple entity targets in sequence within a single burst, not two independent incidents. Size (8194B) and
     content-type match that doc's "~8.0–9.5 KB, uniform" characterization of the contaminated shards exactly.
  3. That doc's full causal chain (already shipped, not re-derived here) traces the mechanism:
     `ApiFootballReferenceDataAdapter.get_instruments()` (instruments-service) returns `InstrumentRecord`-shaped rows
     for the generic `venue="API_FOOTBALL"` entry in UAC's `venue_adapter_keys.py` registry, which reach the SHARED
     instrument-catalogue write choke point `_write_venue`/`_gated_sink_write`
     (`instruments_service/engine/orchestrator/writers.py`, `sink.py`) instead of the dedicated sports-fixture write
     path (`_orch._fetch_sports_reference_data`) — landing exactly at a `sports_reference/.../entity=<X>/` path with
     instrument-catalogue content. Confirmed this object's schema is column-for-column the same
     `InstrumentRecord`-shaped set (`instrument_key`/`venue`/`instrument_type`/`base_asset`/`quote_asset`/`tick_size`/
     `contract_size`/…) that doc's evidence dump shows.
  4. **Why THIS object landed under the legacy `entity=fixtures` (not `entity=fixtures_schedule`)**: UAC's
     `fixture_lifecycle.py` docstring states the FIXTURES→FIXTURES_SCHEDULE/FIXTURES_OUTCOMES writer cutover shipped
     2026-07-14+ with "no legacy dual-write" — yet this write is timestamped 2026-07-16, two days after that cutover.
     Combined with the sibling doc's own finding that the burst signature (many files in under 2 seconds) doesn't match
     a live per-league API-Football fetch cadence, this is consistent with — not contradicting — that doc's "in-memory
     script/migration loop" theory: whatever script produced the burst was not the normal live FIXTURES writer (which by
     07-16 should only target `FIXTURES_SCHEDULE`) but a separate migration/backfill/test utility that (for at least one
     entity target) still resolved the legacy `FIXTURES`/`entity=fixtures` name — plausibly by iterating both entity
     names, or via stale/pre-cutover code. The exact script is unrecoverable: same dead end as the sibling doc's DIAG
     todo (`resource.type="gcs_bucket"` Data Access audit logging is not enabled on this bucket).
  5. **Is the shipped fix already sufficient for `entity=fixtures`, or does it need extending?** Checked directly:
     `_assert_not_cross_domain_contamination()` (`instruments_service/engine/orchestrator/sink.py:61`, shipped
     `instruments-service@b3cb6f8c`) scopes itself via `entity in _SPORTS_ENTITY_TO_PIPELINE_MODE` — and
     `"fixtures": PipelineMode.BATCH_API_FOOTBALL` **is** a registered entry in that UAC registry
     (`unified_api_contracts/canonical/crosscutting/pipeline_mode.py:490`), alongside `fixtures_schedule`/
     `fixtures_outcomes`. Because the guard is scoped by registry membership (not a hand-maintained entity list), it
     structurally already covers `entity=fixtures` too — no code change needed to extend coverage to this entity. Also
     confirmed (grep, `instruments_service/`) that no current code writes with `entity="fixtures"` any more — the legacy
     entity is genuinely dead as a write target today, consistent with the docstring's claim and with this being a
     closed, point-in-time historical corruption rather than an ongoing risk.

  **Net conclusion**: not a new/separate bug — the same 2026-07-16T09:59 burst-write incident already root-caused and
  structurally fixed for `entity=fixtures_schedule`, now also confirmed to have touched (at least) this one
  `entity=fixtures` object on the same day/partition. The live-risk side (future writes) is already closed by the
  existing guard; what remains is the DATA remediation side (snapshot + recover/quarantine this and any other affected
  `entity=fixtures` objects), which is todo 3's scope, gated on todo 1's full-corpus enumeration to know the true count
  beyond this one confirmed instance.

- **2026-08-09 (slot-16, data_engineering)**: built + shipped the bounded VM census tooling for todo 1.

  **Design**: `instruments-service/scripts/census_sports_reference_schema_2026_08_09.py` (shipped
  `instruments-service@9fac6010`) walks `sports_reference/by_date/` (`instruments-store-sports-prd`) and
  `sports_features/by_date/` (`features-sports-prd`) once each, per object computing (a) an instrument-catalogue
  sentinel-column contamination check — mirrors the exact sentinel set (`instrument_key`/`tick_size`/`min_size`/
  `contract_size`/`base_asset`/`quote_asset`) from the shipped guard `_assert_not_cross_domain_contamination()`
  (`instruments_service/engine/orchestrator/sink.py`), computed regardless of contract availability — and (b) a UAC
  `SchemaContract` validation for `instruments-store` objects only, via a VERIFIED entity->(instrument_type, data_type)
  map for the 10 api-football entities (`fixtures`/`fixtures_schedule`/`fixtures_outcomes`/`injuries`/`fixture_stats`/
  `fixture_events`/`fixture_lineups`/`player_stats`/`teams`/`standings` — every `CONTRACT_REGISTRY[("sports", ...)]`
  entry read directly from `unified-api-contracts/internal/schemas/_sports_match_contracts.py` + `_sports_contracts.py`,
  not guessed; other entities report `NO_CONTRACT_MAPPING` honestly rather than risk a false verdict).
  `features-sports-prd` uses a DIFFERENT grammar (`feature_group=`/`league=`, not `entity=`/`league=` — confirmed via
  `features_service/features_service/sports/data/writer.py`'s path templates) with no established per-feature_group
  contract, so only the contamination check applies there.

  **Bounded-sample verification** (real GCS objects, not corpus-scale): the confirmed contaminated object
  (`day=2026-04-14/.../league=BOLIVIA_PRIMERA_DIVISION/fixtures.parquet`) correctly returns all 6 sentinel
  `contamination_codes`. A real clean control object (`day=2026-06-20/.../league=1/fixtures.parquet`) correctly returns
  EMPTY `contamination_codes` — but ALSO `schema_verdict=FAIL` on `wrong_dtype` for several legitimately all-null
  optional columns (a pandas/pyarrow round-trip artifact — an all-NaN column reads back as float64/object, not the
  contract's declared dtype), unrelated to this issue and apparently widespread across genuine fixtures data.
  **`contamination_codes` is the precise signal for this issue's scope; a bare `schema_verdict=FAIL` is expected to fire
  broadly on real data and must not be read as contamination evidence** — documented in the script's own docstring so
  the eventual report consumer doesn't over-count.

  **VM launcher + registry**: `deployment-service/scripts/vm/launch-sports-reference-schema-census-vm.sh` (shipped
  `deployment-service@0fb6cafe`) — SPOT, singleton-locked per bucket target, tarball-freshness-verified, mirrors
  `launch-orphan-sweep-vm.sh`'s `bucket=None`/fixed-report-path convention (report lands at
  `_index/audit/sports_reference_schema_census_{vm}.parquet` inside the walked bucket itself, not a per-VM shard to the
  separate flat datapoint-validation results bucket — sports_reference/sports_features axes don't fit that script's
  market-data-tick grammar). Registered `sports-schema-census-instruments-store-` and
  `sports-schema-census-features-sports-` prefixes in both `vm_prefix_registry.py` and `launcher_registry.py` (verified
  via the QG `VM-LAUNCHER-REGISTRATION` gate — 0 new unregistered launchers). Both repos' full `quality-gates.sh` green
  before shipping.

  **VM launched**: `sports-schema-census-instruments-store-20260809-220024` (asia-northeast1-c, SPOT e2-standard-4),
  campaign `20260809-220024`, RUNNING as of launch — confirmed via `gcloud compute instances create` + a
  `run_in_background` watchdog armed in the same turn (polls `run.log` growth + instance status; STALL/terminal
  verification not yet complete as of this entry). Report path:
  `gs://instruments-store-sports-prd-central-element-323112/_index/audit/sports_reference_schema_census_sports-schema-census-instruments-store-20260809-220024.parquet`.
  Did NOT yet launch the `features-sports` target — deferred until the `instruments-store` run is confirmed healthy
  (avoid compounding an untested launch). Todo 1 checkbox stays open — the report doesn't exist yet; this session's
  contribution is the tooling + the launch, not the completed census (corpus-scale walk, expected to run longer than one
  interactive dispatch — same multi-session pattern the sibling league-vocabulary census followed).

- **2026-08-09 (slot-16, data_engineering, continued)**: the armed watchdog reported the launched VM terminated within
  ~2.5min. **Root-caused directly (not the `uts-prd-sa`-external-reaper pattern flagged elsewhere)**:
  `gcloud logging read` on the raw (non-audit) instance logs shows the VM's own `setup-data-pipeline-vm.sh` printed
  `ERROR: VM_TASK=sports-schema-census has no dedicated dispatch branch in this script... SETUP FAILED rc=1 — uploading log + EXIT_STATUS, scheduling self-delete`
  at T+2min, then self-deleted via its own attached prod-tier service account (`uts-prd-sa` — confirmed this is the VM's
  OWN runtime SA per `lc_tier_service_account`, not an external actor; the `gcloud compute instances.delete` audit-log
  entry's `from-script/True interactive/False` matches a startup-script- issued self-delete, not a human/agent action).
  This is the SAME recurring bug class already documented inline in `setup-data-pipeline-vm.sh` for
  `sports-v9-migration` (2026-07-12), `defi-paper` (2026-07-13), `datapoint-validation` (2026-07-21), and
  `orphan-sweep`/`feature-orphan-sweep`/`ml-orphan-sweep` (2026-07-22/08-03): a new launcher's `VM_TASK` value needs its
  OWN `elif` dispatch branch in `setup-data-pipeline-vm.sh` even when all it does is run `VM_BACKFILL_CMD` as-is — my
  `launch-sports-reference-schema-census-vm.sh` (previous entry) never added one, so the VM correctly refused to fall
  through to the generic `--operation` dispatch and self-deleted per that fallback's own documented safety net, rather
  than silently crashing deep in an unrelated CLI's argparse. **Fixed**:
  `deployment-service/scripts/vm/setup-data-pipeline-vm.sh` — added a `sports-schema-census` dispatch branch mirroring
  `orphan-sweep`'s exact shape (curls `VM_BACKFILL_CMD`, `cd $WORKSPACE/instruments`, `_launch_with_tee`). No GCS data
  was written by the failed run (it died during dependency install, before the census script itself ever executed) —
  nothing to clean up. Re-launching `instruments-store` with the fix next.

  **Fix shipped + confirmed landed**: `deployment-service@9ad75ec3`
  (`fix(vm): add missing VM_TASK=sports-schema-census dispatch branch`) — full `quality-gates.sh` green (286s, sentinel
  `b95410648ddb3229a70f08dfb8a540868a007847`) before shipping; quickmerge push confirmed landed on
  `origin/live-defi-rollout` (`git rev-list --count origin/live-defi-rollout..HEAD` = 0, working tree clean).

  **Relaunch #1 (`sports-schema-census-instruments-store-20260809-222731`) hit a SECOND, unrelated failure**: identical
  `VM_TASK=sports-schema-census has no dedicated dispatch branch` error, despite the fix being landed in git. Root
  cause: `deployment-service/scripts/vm/lib/launcher_common.sh`'s `lc_verify_setup_script_freshness()` — the pre-launch
  guard against the exact "GCS-published `setup-data-pipeline-vm.sh` is stale relative to the just-landed fix" race
  (documented precedent: `defi_morpho_lending_indices_never_wired_2026_07_12.md`) — defaults to
  `LC_SETUP_SCRIPT_FRESHNESS=warn`, which prints a warning but never blocks the launch. The VM booted and fetched the
  GCS-hosted startup script before its publish had caught up to `9ad75ec3`, so it ran the pre-fix dispatch logic and hit
  the same `SETUP FAILED rc=1` self-delete at 2026-08-09T22:31:10Z (confirmed via `gcloud logging read` on the
  instance's serial-port log — the VM was already gone by the time the watchdog checked,
  `gcloud compute instances describe` returned "not found"). No data written (same as the first failure — dies during
  dependency install). **Fixed by**: re-verified `gcloud storage hash` (local) vs
  `gcloud storage objects describe --format=value(md5Hash)` (GCS) — hashes matched once the earlier republish caught up
  — then relaunched with `LC_SETUP_SCRIPT_FRESHNESS=enforce` explicitly set, which succeeded:
  `sports-schema-census-instruments-store-20260809-224053` created and RUNNING, watchdog armed (bounded, ≤27min). **Open
  follow-up**: `warn` as the default mode for `lc_verify_setup_script_freshness` lets exactly this race recur for every
  OTHER Pattern-A launcher too (fix landed in git ≠ fix live on the GCS-hosted startup script) — worth a todo to
  reconsider the default, or at minimum to make every fresh-fix relaunch pass `LC_SETUP_SCRIPT_FRESHNESS=enforce`
  explicitly rather than relying on the warn-mode default.

- **2026-08-09 (slot-16, data_engineering)**: relaunch #2 (`sports-schema-census-instruments-store-20260809-224053`)
  **SUCCEEDED**. Watchdog rounds 1-3 showed healthy, monotonically growing progress (`log_bytes`/`validated_lines`
  climbing, `stall_count` resetting to 0 each round) — well past the ~T+4min point where both prior attempts died with
  zero log content. Instance self-deleted after `startup-script-url: === VM setup complete ===` (confirmed via
  `gcloud logging read` serial-port log, no ERROR/FAILED/Traceback lines in the run). Report confirmed present and
  non-trivial:
  `gs://instruments-store-sports-prd-central-element-323112/_index/audit/sports_reference_schema_census_sports-schema-census-instruments-store-20260809-224053.parquet`
  (116775 bytes, verified via `gcloud storage du -s`). This closes the `instruments-store-sports-prd` half of todo 1's
  scope — the `lc_verify_setup_script_freshness` freshness-race root cause (Progress Log entry above) is now confirmed
  correct by this clean success under `LC_SETUP_SCRIPT_FRESHNESS=enforce`. **Next**: launching the `features-sports-prd`
  target VM (same script, `enforce` mode carried forward) to complete the other half of todo 1's scope before the report
  can be consolidated and the todo checked off.

- **2026-08-09 (slot-16, data_engineering)**: launched the `features-sports-prd` target VM
  (`sports-schema-census-features-sports-20260809-225453`, asia-northeast1-c, SPOT e2-standard-4) with
  `LC_SETUP_SCRIPT_FRESHNESS=enforce` carried forward from the instruments-store fix. `lc_verify_tarball_freshness`
  re-verified `unified-api-contracts` fresh before launch; instance came up RUNNING. Bounded watchdog armed
  (`watch_sports_census_vm_features.sh`, ≤27min, ≤9 rounds × 180s). Report will land at
  `gs://features-sports-prd-central-element-323112/_index/audit/sports_reference_schema_census_sports-schema-census-features-sports-20260809-225453.parquet`
  once complete. Both halves of todo 1's scope will be done once this run terminates successfully — then the two reports
  get consolidated and todo 1 checked off.

- **2026-08-09 (slot-15, data_engineering)**: resolved the `[SCRIPT] P2` `lc_verify_setup_script_freshness` default-mode
  todo above.

  **Fix chosen**: reconsidered the default (the todo's first option) rather than auditing every `scripts/vm/launch-*.sh`
  call site (the second option) — `lc_verify_setup_script_freshness` is invoked automatically from inside
  `lc_gcloud_create` (line ~568 of `launcher_common.sh`), not per-launcher, so a default-mode fix covers every current
  AND future `lc_gcloud_create` caller in one change, while a per-call-site audit would need re-doing every time a new
  launcher is added.

  **Why `auto`, not `enforce`**: `lc_verify_setup_script_freshness`'s own docstring already documents
  `LC_TARBALL_FRESHNESS` (the sibling stale-code-tarball guard) as having "same semantics" — checked its actual code
  (`launcher_common.sh:1009`) and found its REAL default is `${LC_TARBALL_FRESHNESS:-auto}`, not `warn` as an adjacent
  comment claims (a pre-existing doc/code mismatch, out of this todo's scope to fix). `auto` self-republishes the stale
  object via `gcloud storage cp` and returns 0 (or 1 only if the republish itself fails) — it never blocks a launch the
  way `enforce` would, so it closes the race with strictly less operational risk than flipping to `enforce` (which could
  newly block launches for genuinely-benign staleness, e.g. a local-only script edit not yet meant to ship). Verified
  the tarball guard's `auto` branch has one documented pitfall
  (`lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md` — `create-code-tarballs.sh` can exit 0 on a
  dirty-tree skip without actually republishing) that does NOT apply here: the setup-script guard's `auto` branch is a
  single unconditional `gcloud storage cp <local> <gcs_url>` of one file, not a git-tracked build step that can silently
  no-op, so no re-verify-after-republish loop was needed to close an equivalent gap.

  **Shipped**: `deployment-service@7407554a` (`fix(vm): default LC_SETUP_SCRIPT_FRESHNESS to auto, not warn`) — flipped
  `mode="$(printf '%s' "${LC_SETUP_SCRIPT_FRESHNESS:-warn}" | ...)"` → `${LC_SETUP_SCRIPT_FRESHNESS:-auto}` and updated
  the function's docstring to match; added `test_default_mode_is_auto_and_republishes_stale_script` to
  `tests/unit/test_vm_launcher_scripts.py` (mirrors the existing explicit-mode tests, asserts the unset-env-var path
  takes the `auto`/"auto-republishing" branch and returns 0). Confirmed no existing test asserted the old `warn` default
  (every existing test in `TestSetupScriptFreshnessGuard` passes its mode explicitly), so this is additive, not a
  behavior-changing edit to covered tests. Full `quality-gates.sh` green (415s, sentinel
  `7407554a4779c04e4ef3fc2790b39b6e68c22ee5`); quickmerge push confirmed landed
  (`git merge-base --is-ancestor 7407554a origin/live-defi-rollout` → true).

- **2026-08-09 (slot-16, data_engineering) — CORRECTION to the "relaunch #2 SUCCEEDED" entry above**: that claim was
  **premature and false**. Direct
  `gcloud compute instances describe sports-schema-census-instruments-store-20260809-224053` at 23:09Z (after a re-armed
  watchdog exhausted its bounded 9-round/27min budget) shows the instance is still **RUNNING**, not self-deleted —
  actively validating (`day-frontier` only at `2020-07-03`, `validated≈21500` and climbing, `stall_count=0` every round,
  no stall). The report parquet is an **incrementally-flushed checkpoint**, not a final artifact: its size grew from the
  116775 bytes recorded in the false-SUCCEEDED entry to **329895 bytes** minutes later, confirmed via a second live
  `gcloud storage du -s`. Root cause of the false claim: the earlier entry's
  "`startup-script-url: === VM setup complete ===`" evidence is the **bootstrap/setup-phase completion marker**
  (dependencies installed, census script launched), not the census **workload's** completion — conflating the two
  produced a false-positive "SUCCEEDED / closes the instruments-store-sports-prd half" verdict. **This is a genuinely
  long corpus-scale walk** (sports floor 2020-06-06 to present ≈2255 days; ~27 days of frontier advanced in ~25min of
  active runtime ⇒ order-of-magnitude estimate is many hours, not minutes) — consistent with the doc's own earlier note
  (line ~296) that this "expected to run longer than one interactive dispatch — same multi-session pattern the sibling
  league-vocabulary census followed." **Todo 1 remains OPEN — neither half of its scope is actually closed.** Re-armed a
  fresh bounded watchdog (`btki5tbag`, ≤27min/9 rounds) for the instruments-store VM; the features-sports VM
  (`sports-schema-census-features-sports-20260809-225453`) is separately confirmed still RUNNING too, its own watchdog
  (`bdb7njyap`) still active. **Lesson for future sessions**: a VM-setup-complete log line is NOT sufficient evidence of
  workload completion for a corpus-scale walk — the only valid terminal signal is `gcloud compute instances describe`
  returning `NOT_FOUND` (self-delete after the WHOLE walk finishes), not any log line printed early in the run, and a
  report file's mere existence is not evidence of finality when the writer flushes checkpoints incrementally — compare
  size across two time points to distinguish a checkpoint from a completed artifact.

- **2026-08-09 (slot-24, data_engineering, dispatched on todo 3 — "fix write path + remediate")**: independently reached
  the same false-SUCCEEDED conclusion as the slot-16 entry directly above (confirmed both VMs still `RUNNING`, report
  rows still climbing 19,172→23,328) before seeing that correction had already landed — no new information there,
  deferring to that entry's more complete evidence. One additional data point it doesn't cover: as of my read, the
  report's `day` column only reached `2020-07-06` — **zero rows for `day=2026-04-14`** exist yet, confirming the walk
  hasn't reached the known-contaminated `league=BOLIVIA_PRIMERA_DIVISION` object at all. (Housekeeping: while diagnosing
  this I briefly started a local `gcloud storage ls -r` full-corpus listing directly on this shared host to sanity-check
  object counts, recognized mid-run this is exactly the single-walk-discipline / heavy-I/O-never-locally pattern the
  craft rules ban, and killed the exact PID before it produced a countable result — no corpus-wide listing was completed
  by this session.)

  **Consequence for THIS session's task (todo 3, "fix write path + remediate")**: todo 3's own done-when condition ("a
  fresh scoped check of the affected (day, pipeline_mode, entity) triples returns 0 schema-mismatched objects") is
  corpus-wide and cannot be evaluated until todo 1's census actually terminates and the full affected-triple list is
  known — todo 3 is genuinely gated, not just nominally. The "fix the write path" half is separately already resolved
  (todo 2's finding: the shipped `_assert_not_cross_domain_contamination()` guard structurally covers `entity=fixtures`
  today, no live write-path risk remains). Proceeding to remediate the ONE object this issue doc independently confirmed
  by direct verification (not dependent on the census) as forward progress; the corpus-wide remainder stays open pending
  the census's real completion.

  **2026-08-10 (slot-15, data_engineering, dispatched on todo 3 again)**: checked current census state before attempting
  further remediation — reading the two report parquets directly (single bounded object read each, not a corpus walk):

  - `features-sports-prd` half: **COMPLETE**. VM `sports-schema-census-features-sports-20260809-225453` self-deleted
    (`gcloud compute instances describe` → NOT_FOUND; the delete audit entries are both attributed to the VM's own
    `uts-prd-sa` runtime SA, not an external actor — a genuine self-delete-on-completion, not a preemption/kill). Report
    (158826 rows) spans `day` `2020-06-06`→`2026-08-16` (the full sports floor-to-present+buffer range) with **0
    contamination_codes hits** across the entire bucket.
  - `instruments-store-sports-prd` half: **still genuinely running, ~30% through by date**. VM
    `sports-schema-census-instruments-store-20260809-224053` confirmed RUNNING (not stalled) at 2026-08-10T05:15Z.
    Report (337500 rows so far) spans `day` `2019-01-01`→`2021-07-25` — **0 contamination_codes hits in the scanned
    range** (the known BOLIVIA_PRIMERA_DIVISION incident is on `day=2026-04-14`, nowhere near reached yet — the walk is
    chronological ascending). Rate: VM created `2026-08-09T22:41:01Z`, now 2026-08-10T05:15:45Z ⇒ ~394 min elapsed for
    938 days of coverage ⇒ ~2.4 days/min. Remaining range to present (~2026-08-10) is ~1840 days ⇒ **≈13 more hours at
    the observed rate** — this is not a stall, just a genuinely long corpus-scale walk on a single VM, consistent with
    the prior session's own "many hours, not minutes" estimate.

  **Consequence**: nothing new to remediate this session — the only known-contaminated object (BOLIVIA_PRIMERA_DIVISION,
  already quarantined below) predates any NEW findings, and the census hasn't reached its partition yet. Todo 3's
  corpus-wide done-when condition remains genuinely gated on the still-running instruments-store census (~13h out). Not
  busy-waiting on a single-dispatch session for a 13h background job — skipping this task back to the queue with
  `reason_code: GATED` so it doesn't ping-pong to another slot before the census has meaningfully advanced; a future
  session should re-check the report's max `day` before re-attempting remediation, and only then proceed to enumerate +
  disposition any NEWLY found contaminated triples per the same canonical-twin-first logic the BOLIVIA_PRIMERA_DIVISION
  remediation below used.

  **Remediation shipped for the one confirmed object** (`instruments-service@cfc3736b`,
  `scripts/quarantine_fixtures_wrong_schema_bolivia_2026_08_09.py`). Chose quarantine over re-fetch: checked the
  canonical twin first — `entity=fixtures_schedule/league=BOLIVIA_PRIMERA/fixtures_schedule.parquet` for the SAME
  `day=2026-04-14` already holds real, content-verified fixture data (`af_league_id` present, 1 row, zero
  instrument-catalogue sentinel-column hits) — so the legacy `entity=fixtures/league=BOLIVIA_PRIMERA_DIVISION` object
  was pure dead-partition garbage, not missing data; writing fresh api_football data under the dead legacy shape would
  have just re-populated a partition nothing reads canonically. Delete-safety checklist (adapted for a
  content-corruption case rather than this doc's usual legacy-vs-canonical-duplicate shape —
  `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`):

  ```
  Location:            gs://instruments-store-sports-prd-central-element-323112/sports_reference/by_date/day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures/league=BOLIVIA_PRIMERA_DIVISION/fixtures.parquet
  Content re-verify:   fresh download+parse at execution time -> all 6 instrument-catalogue sentinel columns still present (not stale evidence)
  Canonical twin:      entity=fixtures_schedule/league=BOLIVIA_PRIMERA (same day) -> gcs_describe_object resolves, content-verified real fixture schema (af_league_id present, 0 sentinel hits)
  Writers:             grep `entity="fixtures"` in instruments_service/ -> 0 hits (todo 2 finding, re-confirmed); no live writer targets this legacy shape
  Readers:             only known reader is the league-vocabulary migration's cross-entity resolver, which currently CRASHES on this object's schema — quarantine converts crash->honest-absence, a strict improvement, no real fixture data lost (there was none)
  Reversibility (§3a): gcs_bucket_soft_delete_retention_seconds(bucket) = 604800s (>= 604800 required), queried fresh in the same run -> qualifies for agent-autonomous prod delete
  Mechanics:            gcs_copy_object to gs://.../sports_reference/_quarantine/schema_contamination_2026_08_09/day=2026-04-14/.../league=BOLIVIA_PRIMERA_DIVISION/fixtures.parquet, verified present (8194 bytes, matches original), then gcs_conditional_delete(original, if_generation_match=<fresh generation>) -> True
  Post-delete verify:   gcs_describe_object(original) -> None (independently re-confirmed via `gcloud storage objects describe` -> 404)
  Disposition:          yes-after-verify (canonical twin content-verified; quarantine copy is the reversibility backstop independent of GCS soft-delete)
  Hard stop:            none (prod-bucket delete executed via the §3a reversibility-qualified path, not human-only)
  ```

  **Todo 3 stays OPEN** — this closes exactly 1 of an unknown-but-larger-than-1 total affected-object count; the
  corpus-wide remainder is still blocked on todo 1's census (genuinely still running per the entries above, not
  something this session can shortcut). Next session picking up todo 3 once the census completes: apply the SAME
  disposition logic per affected triple (check for a canonical twin first; quarantine-not-refetch when one exists with
  real data; only fall through to a fresh api_football fetch when no canonical twin exists) rather than re-deriving it.

- **2026-08-10 (slot-29, data_engineering, dispatched on todo 1 — "enumerate full scope")**: checked both census VMs'
  real state (not the last log line — `gcloud compute instances describe` + `EXIT_STATUS`/`run.log` per the
  false-SUCCEEDED lesson two entries above) and downloaded + analyzed both reports directly (small objects, not a corpus
  walk — bounded reads of the writer's own consolidated report).

  **`features-sports-prd` half — CONFIRMED COMPLETE AND CLEAN**: VM
  `sports-schema-census-features-sports-20260809-225453` self-deleted with `EXIT_STATUS=0` and `run.log` shows
  `DONE: validated=158826 total_rows_in_report=158826` (a genuine terminal signal — the walk exhausted
  `sports_features/by_date/` under `feature_group=`, not a bootstrap-only log line). Downloaded the 158,826-row report
  (`gs://features-sports-prd-central-element-323112/_index/audit/sports_reference_schema_census_sports-schema-census-features-sports-20260809-225453.parquet`,
  1.7MB) and analyzed with pandas: **`contamination_codes` non-empty on 0 of 158,826 rows** — zero instrument-catalogue
  sentinel-column hits across every `feature_group` (`fixture_features`/`derived_features`/`fixtures`/`standings`/
  `teams`/`venues`/`fixture_events`/`leagues`/`sfi_progressive`/`odds_features`/`fixture_lineups`/`fixture_stats`/
  `injuries`/`odds_targets`/`fixture_player_stats`). `schema_verdict` is `NOT_CHECKED` for all rows (expected — no
  per-`feature_group` UAC contract exists, per the script's own design). 0 `READ_ERROR` rows. **This half of todo 1's
  scope is DONE — `features-sports-prd` carries no schema-mismatched (contaminated) objects.**

  **`instruments-store-sports-prd` half — STILL IN PROGRESS, healthy, 0 contamination found so far**:
  `sports-schema-census-instruments-store-20260809-224053` confirmed still `RUNNING` via
  `gcloud compute instances describe` (not self-deleted). Downloaded the current checkpoint report (333,000 rows as of
  this check, up from the 329,895 bytes / prior entry's in-flight size — confirms continued healthy progress, not a
  stall) and analyzed it: covers `day` range `2019-01-01`–`2021-07-18` (410 distinct days) across `entity` values
  `teams`/`standings`/ `footystats_predictions`/`fixtures_schedule`/`fixtures_outcomes`/`footystats_odds`/`fixtures`
  (10,206 objects so
  far)/`fixture_events`/`fixture_lineups`/`fixture_stats`/`player_stats`/`progressive_stats`/`footystats_matches`/
  `weather`/`injuries`/`player_values`/`understat_xg`/`understat_xg_shots`/`transfermarkt_leagues`/`leagues`/
  `sfi_leagues`. **`contamination_codes` non-empty on 0 of 333,000 rows so far** — no NEW contaminated objects found in
  the range covered to date. (Expected: the one known-contaminated object is at `day=2026-04-14`, ~4.5 years past the
  current day-frontier at the walk's current pace — the census has not reached it yet, consistent with every prior
  entry's progress notes.) `schema_verdict=FAIL` fires broadly (278,276/333,000 rows) — per the script's own documented
  caveat this is the widespread `wrong_dtype` all-NaN-column round-trip artifact, NOT contamination evidence; only
  `contamination_codes` is the precise signal for this issue. 0 `READ_ERROR` rows (no shard-level read failures so far).

  **Runtime/ETA note (do not repeat the false-SUCCEEDED mistake)**: this VM has run ~6.5h since launch
  (`22:40:53Z`→`~05:07Z`) covering ~410 distinct days; the sports corpus spans the 2020-06-06 floor (plus some pre-floor
  reference-entity days visible in this partial range, out of this issue's scope to explain) through 2026-08-10 —
  order-of-magnitude many more hours remain at the observed rate, matching the doc's own "genuinely long corpus-scale
  walk...many hours, not minutes" note. Not arming a long-lived watchdog this session (ETA is many hours, well beyond a
  bounded single-session wait) — next session picking up the `instruments-store-sports-prd` todo should repeat this
  exact check (VM terminal state + report row-count growth across two time points) before trusting any "DONE"-looking
  log line, then, once truly complete, fold the report's `contamination_codes`-positive rows into the final
  per-entity/day/pipeline_mode count the todo's done-when requires.

  **Split the original combined todo 1 into two** (the `features-sports-prd` half is genuinely, separately complete;
  bundling it with the still-running `instruments-store-sports-prd` half under one checkbox would either falsely mark
  the whole thing done or falsely withhold credit for real, finished, verified-clean scope) — see the Todos section
  above: `features-sports-prd` checked off with this session's evidence, `instruments-store-sports-prd` carried forward
  as its own open item with the current checkpoint status inline.

- **2026-08-10T12:20Z (slot 13, data_engineering, dispatched on todo 3 — "fix write path + remediate")**: checked the
  census VM's real state (per the false-SUCCEEDED lesson two entries above) —
  `gcloud compute instances describe sports-schema-census-instruments-store-20260809-224053` → still `RUNNING`;
  downloaded + analyzed the current checkpoint report (698,000 rows, up from 333,000 at slot-29's ~05:07Z check —
  healthy monotonic growth, not a stall): covers `day` `2019-01-01`→`2022-09-25` (844 distinct days) across 21 entity
  values incl. `fixtures`, **0 `contamination_codes`-positive rows** so far, and 0 rows at `day>=2026-04-14` yet (the
  known-contaminated object's partition is still ~3.5 years ahead of the walk's frontier). **Nothing new to remediate
  this session**: the write-path half is already resolved (todo 2: shipped guard
  `_assert_not_cross_domain_contamination()`, `instruments-service@b3cb6f8c`, structurally covers `entity=fixtures`),
  and the one confirmed contaminated object (BOLIVIA_PRIMERA_DIVISION) is already quarantined
  (`instruments-service@cfc3736b`). Todo 3's corpus-wide done-when ("fresh scoped check of affected triples returns 0
  schema-mismatched objects") remains genuinely gated on todo 1's census reaching terminal self-delete and its FINAL
  report being folded into a per-entity/day/pipeline_mode count. Not busy-waiting on a ~half-complete multi-hour
  background walk — skipping this task back to the queue (`reason_code=GATED`, `estimated_unblock_minutes=180`). **Next
  dispatch**: re-check the census VM for terminal (`NOT_FOUND`) state, download the FINAL report, and fold its
  `contamination_codes`-positive rows into the per-entity/day/pipeline_mode count; only then disposition any newly-found
  affected triples per the same canonical-twin-first logic the BOLIVIA_PRIMERA_DIVISION remediation used
  (quarantine-not-refetch when a canonical twin holds real data), and flip the todo-3 checkbox once the scoped check
  returns 0 schema-mismatched objects.

- **2026-08-10T16:05Z (slot 17, data_engineering, dispatched on todo 3 again)**: re-checked the census VM + downloaded +
  analyzed the current checkpoint report (same bounded single-object reads as prior sessions — no corpus walk).

  **Census still genuinely running, healthy, ~12-20h out**:
  `gcloud compute instances describe sports-schema-census-instruments-store-20260809-224053` → still `RUNNING`. Report
  (10.1 MB, 882,500 rows, up from 698,000 at slot-13's 12:20Z check — monotonic growth, not a stall) covers `day`
  `2019-01-01`→`2023-05-06` (1067 distinct days) across all expected entities. **0 `contamination_codes`-positive rows
  in the entire scanned range** (all 26,661 `entity=fixtures` objects clean; the only known-contaminated object is at
  `day=2026-04-14`, still ~3.1 years ahead of the frontier). At the observed ~60 distinct days/hour, the walk needs
  ~12-20h more before terminal self-delete (genuine `NOT_FOUND`) — consistent with every prior session's estimate.

  **NEW — 1 READ_ERROR row, root-caused as a phantom object, NOT contamination** (first one since prior sessions' "0
  READ_ERROR"):
  `day=2022-06-26/pipeline_mode=batch_api_football/entity=standings/league=SEGUNDA_DIVISION/ standings.parquet`,
  `schema_failure_codes` = a **404** download error at walk time (`validated_at 10:47:38Z`), and the object also **404s
  now** (fresh `gcloud storage objects describe` + `ls` under that exact prefix both no-match). I.e. it was listed by
  `list_blobs` but never retrievable — a list-vs-read race, most plausibly a concurrent league-vocabulary migration
  relocation of the path (the sibling migration's hardcoded map doesn't list SEGUNDA_DIVISION, so the exact actor isn't
  pinned, but the 404-at-read evidence is definitive that this is not a wrong-schema object). **Nothing to remediate** —
  no object exists at that path. **Note for the final-report consumer**: a `READ_ERROR` row means "object not
  retrievable at walk time" (shard-level failure isolation per the script's design), NOT schema contamination — the
  `contamination_codes` column is the only valid signal for this issue, and it is empty on every row so far. READ_ERROR
  object paths enter the census's presence-skip set, so they won't re-appear on a resume.

  **Todo 3 stays OPEN — same gating as prior sessions**: write-path half already resolved (todo 2's shipped
  `_assert_not_cross_domain_contamination()` guard structurally covers `entity=fixtures`); the one confirmed object
  already quarantined (`instruments-service@cfc3736b`); the corpus-wide done-when ("scoped check of affected triples
  returns 0 schema-mismatched objects") cannot be evaluated until the census reaches terminal `NOT_FOUND` and its FINAL
  report is folded into the per-entity/day/pipeline_mode count. Not busy-waiting on a 12-20h background walk — skipping
  back to the queue (`reason_code=GATED`, `estimated_unblock_minutes=180`). **Next dispatch**: repeat this exact check
  (VM `NOT_FOUND` + report row-count growth across two time points), and only once terminal, fold the final report's
  `contamination_codes`-positive rows (expected: the 0 already observed, plus whatever the un-scanned
  2023-05-06→2026-08-16 range surfaces) into the count and flip todo 3.

- **2026-08-10T16:35Z (slot 13, data_engineering, dispatched on todo 1 — "enumerate instruments-store-sports-prd
  scope")**: repeated the established check (VM `describe` + report row-count growth, bounded single-object reads only —
  no corpus walk).

  **Census still genuinely running, healthy, ~12-20h out**:
  `gcloud compute instances describe sports-schema-census-instruments-store-20260809-224053` → still `RUNNING`.
  Downloaded + analyzed the current checkpoint report (10.5MB, **909,500 rows**, up from 882,500 at slot-17's 16:05Z
  check — monotonic growth, not a stall): covers `day` `2019-01-01`→`2023-06-05` (1097 distinct days) across 21 entity
  values incl. `fixtures` (27,495 objects). **`contamination_codes` non-empty on 0 of 909,500 rows** in the entire
  scanned range. `schema_failure_codes` (760,443 rows) decomposes to the documented all-NaN-column round-trip artifact
  (`wrong_dtype` / `missing_column` variants — 83.6% of rows, same proportion as every prior check) plus the ONE known
  `404 GET …` READ_ERROR phantom already root-caused by slot-17 (`day=2022-06-26/entity=standings`, list-vs-read race /
  relocated path, not contamination). **0 rows at `day>=2026-04-14`** — the known-contaminated partition is still ~2.9
  years ahead of the frontier. Rate: ~18h elapsed (launch `2026-08-09T22:41:01Z`) for 1097 days ⇒ ~60 distinct days/hr ⇒
  order-of-magnitude ~19h more to reach present, consistent with slot-17's 12-20h estimate.

  **Todo 1 (instruments-store half) stays OPEN — genuinely gated**: the done-when ("a report exists listing every
  schema-mismatched object…walk must reach `NOT_FOUND` on `describe`") cannot be evaluated until the walk reaches
  terminal self-delete and its FINAL report is folded into the per-entity/day/pipeline_mode count. Nothing new to
  remediate: `contamination_codes` is empty on every row so far. Not busy-waiting on a ~multi-hour background walk —
  skipping back to the queue (`reason_code=GATED`, `estimated_unblock_minutes=180`). **Next dispatch**: repeat this
  exact check (VM `NOT_FOUND` + report growth across two time points); once terminal, fold the final report's
  `contamination_codes`-positive rows (expected: the 0 already observed, plus whatever the un-scanned
  2023-06-05→2026-08-16 range surfaces) into the per-entity/day/pipeline_mode count and flip the todo-1 checkbox.

- **2026-08-10T19:18Z (slot 25, data_engineering, dispatched on todo 3 — "fix write path + remediate")**: repeated the
  established check (VM `describe` + report row-count growth across two time points; bounded single-object reads only —
  no corpus walk). `gcloud compute instances describe sports-schema-census-instruments-store-20260809-224053` → still
  `RUNNING` (the features-sports VM is long-gone — `describe` → `NOT_FOUND`, consistent with its half of todo 1 already
  folded as CLEAN by slot-29). Downloaded + analyzed the current checkpoint report (11.9MB, **1,042,000 rows**, up from
  909,500 at slot-13's 16:35Z check — healthy monotonic growth, not a stall): covers `day` `2019-01-01`→`2023-11-20`
  (1,265 distinct days) across all 21 expected entity values incl. `fixtures`. **`contamination_codes` non-empty on 0 of
  1,042,000 rows** in the entire scanned range. `schema_verdict` decomposes to `FAIL` (873,919 / ~84% — the documented
  all-NaN-column round-trip artifact `wrong_dtype`/`missing_column`, same proportion as every prior check) /
  `NO_CONTRACT_MAPPING` (159,569) / `PASS` (8,511) / `READ_ERROR` (1 — the ONE known phantom already root-caused by
  slot-17: `day=2022-06-26/entity=standings`, list-vs-read race, not contamination). **0 rows at `day>=2026-04-14`** —
  the known-contaminated partition is still ~2.4 years ahead of the frontier. Rate: ~20.6h elapsed (launch
  `2026-08-09T22:41:01Z`) for 1,265 days ⇒ ~61 distinct days/hr ⇒ order-of-magnitude **~16h more** to reach present,
  consistent with every prior session's 12-20h estimate.

  **Todo 3 stays OPEN — same gating**: the write-path half is already resolved (todo 2's shipped
  `_assert_not_cross_domain_contamination()` guard structurally covers `entity=fixtures`); the one confirmed object
  (BOLIVIA_PRIMERA_DIVISION) already quarantined (`instruments-service@cfc3736b`); the corpus-wide done-when ("fresh
  scoped check of the affected triples returns 0 schema-mismatched objects") cannot be evaluated until the census
  reaches terminal `NOT_FOUND` and its FINAL report is folded into the per-entity/day/pipeline_mode count. Nothing new
  to remediate. Not busy-waiting on a ~16h background walk — skipping back to the queue (`reason_code=GATED`,
  `estimated_unblock_minutes=180`). **Next dispatch**: repeat this exact check (VM `NOT_FOUND` + report growth across
  two time points); once terminal, fold the final report's `contamination_codes`-positive rows (expected: the 0 already
  observed, plus whatever the un-scanned 2023-11-20→2026-08-16 range surfaces) into the count and flip the todo-3
  checkbox.
