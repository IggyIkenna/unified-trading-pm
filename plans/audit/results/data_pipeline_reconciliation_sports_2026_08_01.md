---
doc_type: audit-result
title: "Data-pipeline reconciliation — sports (2026-08-01)"
summary: >-
  Tier-1 (in-session, no VM) four-surface canonicalisation reconciliation of asset_group=sports, raw-tick layer only,
  over PROD buckets (read-only). market-data-tick-sports-prd resolves and is reachable; consolidator healthy. CONTINUITY
  CHECK: the 2026-07-24 report's headline F1 finding (manifest-staleness since 2026-07-20) is CONFIRMED RESOLVED — an
  addendum was already filed 2026-07-24 to sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md and
  root-caused/closed 2026-07-26 (deliberate 2026-06-07 architecture: sports' canonical availability manifest lives in
  instruments-store-sports-prd, not market-data-tick-sports-prd — working as designed, not a bug). NEW HEADLINE (F5):
  while verifying F1's resolution held, found a DIFFERENT, currently-active, live production incident — the shared Cloud
  Run Job uts-prod-market-tick-data-service-fast-t1-recon has been OOM-killing on nearly every SPORTS execution since
  ~2026-07-27 (846/846 sampled ERROR log entries in this pass carry --asset-group SPORTS), producing a REAL (not
  manifest-lag) GCS-side capture gap: ZERO raw_tick_data objects for day=2026-07-30, 2026-07-31, and 2026-08-01 (partial
  day at check time), confirmed via direct listing AND independently corroborated by the canonical
  instruments-store-sports-prd manifest showing the same max-date=2026-07-29 ceiling. Filed as a new issue doc
  (sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md) — proximate cause (OOM) confirmed live via gcloud
  logging; underlying memory-blowup root cause NOT yet found (out of scope for this read-only audit). Path structure
  remains canonical (oracle: 0/25 violations, both require_pipeline_mode settings, sample includes the new fixture_id=
  path segment). Distinct-value venue census improved since 07-24: non-canonical/non-accepted venue rows now 9.06% of
  the manifest (56,953/628,446, down from 12.3%) — the registries were expanded (UNIBET_UK, UNIBET_EU, BET888SPORT,
  LADBROKES, SMARKETS, FOOTYSTATS, BETOPENLY, NOVIG, ONEXBET, PROPHETX now canonical/accepted) but KALSHI's 20,785-row
  cross-AG bleed is UNCHANGED (still open), SPORT888/LADBROKES_UK grew in volume, and a new minor anomaly
  (venue='FOOTBALL', 44 rows, single historical day, all attempted_failed) surfaced. No new non-canonical GCS location
  found beyond the already-registered items; processed_candles/ now exists alongside processed/ in this bucket
  (candles-layer, out of scope, noted for the register). No delete suggestions. Sports raw-tick is NOT 100% canonical,
  and the standout live-correctness risk right now is F5, not F1/F2.
status: partial
nature: record
asset_group: [sports]
stage: [data]
repos:
  [
    unified-trading-pm,
    unified-api-contracts,
    unified-trading-library,
    market-tick-data-service,
    instruments-service,
    deployment-service,
  ]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, four-surface, sports, manifest, oom, live-outage, venue-census, big-finding]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    gcs-and-manifest-delete-safety-protocol,
    non-canonical-path-inventory,
    canonical-cutover-register,
    orphan-object-detection,
    data_pipeline_reconciliation_sports_2026_07_20,
    data_pipeline_reconciliation_sports_2026_07_22,
    data_pipeline_reconciliation_sports_2026_07_24,
  ]
created: 2026-08-01
resulting_plan:
lib_version:
doc_versions_checked:
audited_scope:
  "asset_group=sports, raw-tick layer only, PROD (-prd-) buckets only, read-only. Primary: market-data-tick-sports-prd
  full manifest read (predicate/column-projected, 628,446 rows), 25-object oracle sample, 3-object schema-validation
  sample, live GCS delimiter descent (multiple days incl. the 07-27..08-01 gap window), distinct-value venue census
  (full manifest vs UAC registries), S4 catalogue grep, live gcloud logging/scheduler/secret inspection to root-cause
  the F5 OOM incident. Secondary/cross-check only: instruments-store-sports-prd (manifest max-date cross-check + prior
  index freshness). NOT reconciled: candles layer, Tier-2 100%-corpus per-datapoint validation, full S1<->S3 join,
  code-level root-cause of the F5 memory blowup (flagged as follow-up, not a reconciliation-skill task)."
date: 2026-08-01
auditor: /data-pipeline-reconciliation sports (dispatched sub-agent)
parent_epic: sports_master
severity: P0
---

# /data-pipeline-reconciliation — sports — 2026-08-01 (raw-tick layer)

**Scope**: raw-tick layer only (`--layer candles` explicitly out of scope). PROD buckets only. Tier 1 (in-session, no
VM) — interactive mode, stop after this run. Third of a 3-checkpoint sequence (baseline 07-20, mid 07-22, this = final
08-01) tracked by `sports_consolidated_native_ao_extract_2026_07_25.md` Track K.

## Continuity check — does the 2026-07-24 report's F1 headline still hold?

**No — F1 is CONFIRMED RESOLVED, and correctly so (not a stale claim).** The 2026-07-24 report's own text says a
follow-up issue doc appears not to have been filed; that read of the corpus is **incorrect** — a follow-up WAS filed the
same day, as an addendum to the pre-existing
`plans/active/issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md` (not a brand-new doc, which
is why a slug-pattern search for "F1" specifically doesn't surface it). That addendum's own todo 6 was root-caused and
closed **2026-07-26**: `market_tick_data_service/engine/orchestrator/_manifest_bucket.py::_resolve_manifest_bucket()`
confirms the 2026-06-07 sports-manifest-canonicalisation decision **deliberately** routes sports' canonical availability
manifest to `instruments-store-sports-prd` while raw tick bytes correctly stay in `market-data-tick-sports-prd` —
code-enforced since 2026-07-13, refined 2026-07-21. Todo 8 explicitly ruled disposition (a): leave
`market-data-tick-sports-prd`'s own `_index/` as a documented, intentionally-stale-for-manifest- purposes artifact —
backfilling/repointing it would reintroduce the exact split-brain the 2026-07-13 fix eliminated. **No new issue doc was
needed for F1 itself** — the existing addendum's resolution stands. What follow-up WAS needed is a fresh finding this
pass surfaced while re-checking F1 (see F5 below).

## Phase 0 — resolution gate

### Bucket paths

| kind              | asset_group | resolved bucket                                       | reachable | notes                                                                                                        |
| ----------------- | ----------- | ----------------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------ |
| market-data       | sports      | `market-data-tick-sports-prd-central-element-323112`  | ✅ yes    | **primary bucket for this dispatch** — raw-tick MTDS estate                                                  |
| instruments-store | sports      | `instruments-store-sports-prd-central-element-323112` | ✅ yes    | cross-referenced (manifest max-date cross-check for F5), NOT independently four-surface-reconciled this pass |

Resolved via `resolve_bucket_name(cloud='gcp', kind=..., asset_group='sports', deployment_env='prd')`. No `-test-`
bucket resolved (refusal condition not triggered). Reachability proven by non-recursive top-level listing:

```
market-data-tick-sports-prd-central-element-323112 top-level prefixes:
  _index/  _legacy_migrated_processed/  _legacy_migrated_scripts/  _legacy_migrated_vm_staging/
  _vm_staging/  processed/  processed_candles/  raw_tick_data/  scripts/
```

**New since 2026-07-24**: `processed_candles/` now exists alongside `processed/` (candles-layer, out of scope for this
raw-tick dispatch — noted for the Phase 2 register recheck below, not investigated further).

### Index freshness / lock state (read 2026-08-01T10:37–10:39Z)

| bucket                   | `_index/latest.json`                                                                                    | lock state                                                                                              | `_index/phantom_audit_latest.json`                                                                           |
| ------------------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| market-data-tick-sports  | `last_run_at=2026-08-01T10:37:41Z, success=true, verdict=empty, shards_scanned=1, no_op=true` — healthy | no lock                                                                                                 | **still NOT PRESENT** — declared coverage gap, unchanged since 07-24                                         |
| instruments-store-sports | `last_run_at=2026-08-01T10:37:37Z, success=true, verdict=empty, no_op=true` — healthy                   | **LOCK HELD** (`_index/consolidator.lock`, `started_at=2026-08-01T10:26:29Z`, ~12 min old at read time) | present, `generated_at=2026-07-25T02:23:45Z, phantom_count=0` (7-day-stale, not re-run per skill's own rule) |

The `instruments-store-sports` lock is present but `latest.json` shows a successful completed run 11 minutes AFTER the
lock's `started_at` — ambiguous whether this is a stale/orphaned lock or a fresh run about to release; not treated as a
blocking condition since `latest.json`/`consolidator_stall_state.json` (`streak=0`) both report healthy. Not
investigated further (out of this dispatch's scope; would need a second read a few minutes later to disambiguate).

`market-data-tick-sports-prd`'s `_index/availability_index.parquet` grew from 465,223 rows (07-24) to **628,446 rows**
(07-25T00:57 → 08-01T10:38, size 14.4MB) — a real catch-up write landed 2026-07-25/07-26 (see Continuity check above).
`instruments-store-sports-prd`'s canonical index is now 231.5MB / row count not re-derived this pass (too large for a
full download within this session's budget; only date-scoped queries run against it, per the single-walk / bounded-
compute discipline).

### Suppression inputs loaded

Same as 07-24: `canonical-cutover-register.md` §2 (`require_pipeline_mode` effective 2026-05-19) and §6 (sports
`data_type` casing, `migration_pending`); `reconciliation-finding-taxonomy.md` §4 accepted-exception list;
`non-canonical-path-inventory.md` sports-scoped rows #1/#4/#13.

## Phase 1 — four-surface comparison

### Surface 1 (path) — machine oracle

25-object sample drawn from the current manifest (random, seed=42, spanning dates/venues/leagues), including objects
with the **new `fixture_id=` path segment** observed this pass (not present in the 07-24 sample):

```
violations w/ require_pipeline_mode=False: 0 / 25
violations w/ require_pipeline_mode=True:  0 / 25
```

**Path structure remains canonical (sampled)**, including the newer per-fixture-scoped shape. No id-form/stem check run
(sports is `not_applicable` per this skill's own instruction — sports has no stem rule).

### Surface 2 (content) — spot check + sampled schema validation

Read 3 live objects in full (`day=2026-07-29`, `venue=DRAFTKINGS`, mixed league-level and per-fixture path shapes), ran
`unified_api_contracts.validate_dataframe()` against the resolved
`SchemaContract(asset_group='sports', instrument_type='odds', data_type='trades')`:

| object                                                             | rows | schema violations |
| ------------------------------------------------------------------ | ---- | ----------------- |
| `league_id=ARGENTINA_PRIMERA/fixture_id=1493022/.../ticks.parquet` | 72   | 0                 |
| `league_id=ARGENTINA_PRIMERA/.../ticks.parquet` (no fixture_id)    | 117  | 0                 |
| `league_id=BRASILEIRAO/fixture_id=1492316/.../ticks.parquet`       | 24   | 0                 |

Real bookmaker prices, non-null `instrument_id` (sports' own grammar), all pass the contract. **SAMPLED (n=3), not full
corpus.**

### Surface 3 (manifest) — F1 (resolved) and F5 (NEW — the current headline)

**F1 status: RESOLVED, confirmed above** (Continuity check section). `market-data-tick-sports-prd`'s manifest is
_expected_ to stay behind the live edge by design; that is not itself a defect.

**F5 — NEW, `orphan_class` = real writer-side capture gap (not a manifest artifact), HIGH severity, active as of check
time.** Both `market-data-tick-sports-prd`'s own manifest and the canonical `instruments-store-sports-prd` manifest
independently show `pipeline_mode=batch_odds_api` stopping dead at `date=2026-07-29`:

```
market-data-tick-sports-prd manifest, batch_odds_api rows by date (2026-07-20 onward):
  07-20: 27   07-22: 84   07-23: 40   07-24: 84   07-25: 19,827   07-26: 31,661   07-29: 1,796
  07-27, 07-28, 07-30, 07-31, 08-01: 0 (all)

instruments-store-sports-prd manifest, batch_odds_api rows (07-25 onward):
  07-25: 2,909   07-26: 4,644   07-27: 1,593   07-28: 800   07-29: 1,310
  07-30, 07-31, 08-01: 0 (all)
```

Direct GCS delimiter-scoped listing (not manifest-derived) of `market-data-tick-sports-prd`'s
`raw_tick_data/by_date/day={D}/` for `D` in `{2026-07-29..2026-08-01}` confirms this is **real, not a manifest-lag
artifact**: `day=2026-07-29` has a populated `pipeline_mode=batch_odds_api/` prefix (23 venue sub-prefixes, real
content, confirmed above); `day=2026-07-30`, `2026-07-31`, and `2026-08-01` (today, partial) have **zero pipeline_mode
prefixes of any kind** — nothing was written to GCS at all for those three days as of check time.

**Root cause traced live (not guessed)**: `gcloud logging read` against the shared Cloud Run Job
`uts-prod-market-tick-data-service-fast-t1-recon` found near-total OOM failure —
`"Task ... failed with exit code: 0 and message: The configured memory limit was reached"` (8Gi container limit).
846/846 sampled ERROR entries (2026-08-01T09:00-10:45Z window) carry `--asset-group SPORTS` in the execution's container
args — confirmed SPORTS-specific in this sample. Onset bounded to 2026-07-27 (0 OOM errors at 07-27T00:00-01:00Z, 42 at
07-27T12:00-13:00Z), continuously present through the 2026-08-01T10:43Z check (hourly sample counts ranged 7-255
errors/hour). Cloud Scheduler (`uts-prod-sports-scheduler-cron`, `*/5min`, ENABLED) and the `odds-api-key` credential
(live HTTP 200, `x-requests-remaining: 5000000`) are both confirmed healthy — ruling out the two previously-known sports
capture failure modes (the future-date-guard bug, fixed 07-26; the credential deactivation, rotated 07-29). **Underlying
memory-blowup root cause NOT identified this pass** (would need code-level profiling — out of scope for this read-only
audit). Filed as a new issue doc: `plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md` (full
evidence + recommended next steps there). **This is the standout live-correctness finding of this pass** — bigger and
more urgent than F2/F4 below, and distinct from every previously-tracked sports capture incident.

### Surface 4 (catalogue)

Unchanged from 07-24: `configs/data-catalogue.instruments-service.yaml` (`last_updated: 2026-02-06`) carries a `SPORTS:`
section keyed on provider, not the raw-tick manifest's `venue=` axis — a declared grain-mismatch coverage gap per
`four-surface-reconciliation-procedure.md` §1, reported once, not a fresh finding.

## Phase 1b — distinct-value census (G1)

### F2 — `non_canonical_axis_value`, MEDIUM severity, S3 (manifest column) — IMPROVED since 07-24, but not resolved

Full venue census of the now-628,446-row manifest. **The canonical + accepted registries themselves grew** between 07-24
and today: `VENUES_BY_ASSET_GROUP['sports']` now has 11 entries (added `BET888SPORT`, `LADBROKES`, `SMARKETS` since
07-24's 8), and `SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS` now has 23 entries (added `UNIBET_UK`, `UNIBET_EU`,
`BETOPENLY`, `NOVIG`, `ONEXBET`, `PROPHETX` since 07-24's 20, plus `FOOTYSTATS` reclassified) — real maintenance
progress on the exact class of gap the 07-24 report flagged.

| venue        | rows       | status                                                                                                                                                                                                                                                                                                           |
| ------------ | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| KALSHI       | **20,785** | **NOT canonical, NOT accepted, UNCHANGED count from 07-24** — still the cross-AG (prediction-registered) bleed, still 100% `empty_confirmed`/`row_count=0`, still open (no fix landed)                                                                                                                           |
| SPORT888     | **20,066** | **NOT canonical, NOT accepted** — up from 13,997 (07-24); distinct from now-canonical `BET888SPORT` (18,903 rows) — likely the same unregistered-bookmaker-variant naming, still not folded in                                                                                                                   |
| LADBROKES_UK | **13,560** | **NOT canonical, NOT accepted** — up from 8,859; distinct from now-canonical `LADBROKES` (12,210 rows)                                                                                                                                                                                                           |
| (blank)      | 2,498      | unchanged, blank sentinel, not counted as a finding                                                                                                                                                                                                                                                              |
| FOOTBALL     | **44**     | **NEW this pass** — venue field literally `'FOOTBALL'` (the sport, not a bookmaker); all rows `pipeline_mode=batch_footystats`, `data_type=arbitrage_opportunity`, single historical date `2026-11-26`→ actually `2021-11-26`, 100% `capture_status=attempted_failed` — minor, historical, no real data at stake |

**Total non-canonical, non-accepted: 56,953 rows (9.06% of 628,446)** — down from 57,246/465,223 = 12.3% at 07-24.
UNIBET_UK (9,423 at 07-24), SMARKETS (4,162), UNIBET_EU (12), and UNKNOWN (8) are **no longer flagged** — UNIBET_UK and
UNIBET_EU moved to the accepted list; SMARKETS moved to the canonical list; UNKNOWN's 8 rows were not found in the
current manifest at all (not investigated further — immaterial volume, consistent with normal row churn/dedup). **Net
verdict: real progress on the maintenance-gap class of drift, but the two most consequential slices (KALSHI's cross-AG
bleed, and the SPORT888/LADBROKES_UK unregistered-variant pattern, now larger in absolute rows) remain open.**

## Phase 2 — non-canonical sweep + delete suggestions

### Register re-check (`/codex/02-data/non-canonical-path-inventory.md`)

| register item                                                           | disposition this pass                                                                                                                                                                                                                                                                                  |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| #4 — `scripts/` + `_legacy_migrated_scripts/scripts/` executable Python | **RE-CONFIRMED PRESENT**, same 3 files as 07-24 (`fetch_missing_odds.py`, `oddspapi_historical_backfill.py`, `oddspapi_runner.py`). Disposition unchanged: `unknown`.                                                                                                                                  |
| #13 — `processed/` vs `processed_candles/` naming                       | **UPDATED**: `processed_candles/` now exists (new since 07-24, alongside `processed/` and `_legacy_migrated_processed/`) — candles-layer, out of scope for this raw-tick dispatch, register-worthy for a future `--layer candles` run to investigate whether this represents an in-progress migration. |

**No new non-canonical GCS _location_ (prefix/directory) found this pass** — F5 is a live-writer-outage finding, not a
path-canonicality finding; F2 is an S3 vocabulary drift, not a new location. **No register-patch stanza needed** beyond
the #13 freshness note above (informational, not a structural change to the register).

### Delete suggestions

**None.** Same as every prior pass — no candidate this session carries the 5-part proof.

## Suppressed (accepted exceptions)

- AE-1 (sports blank `pipeline_mode`/`source`) — not re-checked this pass (unchanged condition,
  `instruments-store-sports`-scoped, out of this bucket's primary scope).
- Sports `data_type` casing (`migration_pending`) — not re-measured this pass; no reason to expect it changed.

## Formulas named

- `reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)`, `empty_confirmed` EXCLUDED
  (`honest-coverage-model.md`, CK3-certified). Not recomputed in full this pass (would require a fresh full-manifest
  scan of `capture_status` breakdown) — **flagged as a coverage gap**, not silently assumed unchanged from 07-24's
  degenerate 100%.
- F2's 9.06% = `56,953 / 628,446` (non-canonical-non-accepted venue rows / total manifest rows).
- F5's gap = 3 consecutive days (2026-07-30, 07-31, 08-01-partial) with 0 GCS objects of any kind under
  `raw_tick_data/by_date/day={D}/` in `market-data-tick-sports-prd`, cross-confirmed via `instruments-store-sports-prd`
  manifest agreement on the same `batch_odds_api` max-date=2026-07-29 ceiling.

## Coverage gaps (declared, not silently omitted)

1. **`instruments-store-sports-prd` only spot-checked** (manifest max-date cross-check for F5) — not independently
   four-surface-reconciled this pass.
2. **`--layer candles` not run** — out of scope; the new `processed_candles/` prefix is unexplored.
3. **No Tier-2 (VM, 100%-corpus) per-datapoint validation** — Tier-1 only.
4. **`_index/phantom_audit_latest.json` still absent** for `market-data-tick-sports-prd` — S3 phantom verdict not
   independently checked, unchanged since 07-24.
5. **id-form (G2) canonical-id-builder byte-equality check not run** — sports is `not_applicable` (no stem rule),
   consistent with prior passes.
6. **Full manifest S1↔S3 join not performed** — 25-object oracle sample + 3-object schema sample only.
7. **`reachable_coverage` formula not recomputed** — flagged above, not silently carried forward from 07-24.
8. **The `instruments-store-sports-prd` consolidator lock's staleness (started 10:26:29Z, still held at 10:38:42Z check
   time) was not disambiguated** — a second read a few minutes later would resolve whether it's a live in- progress run
   or an orphaned lock; not investigated further (latest.json/stall_state both report healthy).
9. **F5's underlying memory-blowup root cause not code-level investigated** — proximate cause (OOM) confirmed live; the
   "why does SPORTS' fast-t1-recon dispatch need >8Gi" question is unanswered, tracked as a follow-up todo in the new
   issue doc.

## Big-picture verdict

**Sports raw-tick (`market-data-tick-sports-prd`) is NOT 100% canonical.** Path structure remains clean (oracle: 0
violations, sampled, including the newer per-fixture path shape) and schema validation passes on every sampled object.
The two 07-24 findings resolved/improved as expected: **F1 (manifest staleness) is confirmed genuinely RESOLVED**
(deliberate architecture, closed 2026-07-26, correctly not requiring a new issue doc — the 07-24 report's own "no
follow-up filed" caveat was itself slightly wrong, a follow-up addendum existed the whole time) — and **F2
(venue-vocabulary drift) measurably improved** (12.3% → 9.06%, driven by real registry-maintenance work), though
KALSHI's cross-AG bleed is unchanged and two unregistered-bookmaker slices grew in absolute volume. **The standout
finding this pass is entirely new: F5, a live, currently-active Cloud Run Job OOM outage** that has silently zeroed out
real SPORTS odds capture for at least 3 consecutive days (07-30, 07-31, 08-01-partial) as of check time, distinct from
and immediately following the resolution of the prior month-long capture gap. This is flagged as the priority finding
for operator/worker attention — see the new issue doc for full evidence and recommended next steps. No new non-canonical
GCS location found; no delete suggestions.

## Cross-references filed this pass

- **New issue** (F5): `plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`
- **No new issue needed for F1** — already resolved via the pre-existing addendum to
  `plans/archive/issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md` (closed 2026-07-26,
  confirmed still valid this pass).
