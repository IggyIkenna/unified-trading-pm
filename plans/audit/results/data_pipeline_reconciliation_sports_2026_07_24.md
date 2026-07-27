---
doc_type: audit-result
title: "Data-pipeline reconciliation — sports (2026-07-24)"
summary: >-
  Tier-1 (in-session, no VM) four-surface canonicalisation reconciliation of asset_group=sports, raw-tick layer only,
  over PROD buckets (read-only). market-data-tick-sports-prd resolves and is reachable; consolidator healthy (fresh
  no-op run). HEADLINE: that bucket's OWN manifest has recorded zero new rows across ALL pipeline_modes since
  date=2026-07-20 (4-5 days and growing at run time) while GCS keeps receiving real, populated raw-tick objects daily
  through day=2026-07-24 — a reused 2026-07-21 whole-corpus orphan sweep independently found 20,443 such
  manifest-uncovered objects back to 2021. A same-pass cross-check against the sibling instruments-store-sports-prd
  manifest found a matching row for the one live shard sampled, pointing at a documented cross-bucket manifest-routing
  architecture (not necessarily raw data loss) — but this was NOT verified across the full population. Separately, a
  distinct-value census found 57,246 manifest rows (12.3%) carrying a venue value outside both the canonical vocabulary
  and the existing accepted-exception list, the largest of which (KALSHI, 20,785 rows, all empty_confirmed/row_count=0)
  is registered exclusively under asset_group=prediction, not sports. Also found that this skill's OWN governing codex
  (four-surface-reconciliation-procedure.md SS4.2/SS6) misdescribes the bucket it resolves for sports raw-tick,
  conflating it with a different bucket's reference-data layout. No new non-canonical GCS location found; no delete
  suggestions (insufficient 5-part-proof evidence gathered this pass). Sports raw-tick is NOT 100% canonical.
status: partial
nature: record
asset_group: [sports]
stage: [data]
repos:
  [unified-trading-pm, unified-api-contracts, unified-trading-library, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags:
  [reconciliation, canonicalisation, four-surface, sports, manifest, orphan, cross-bucket, venue-census, codex-accuracy]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    gcs-and-manifest-delete-safety-protocol,
    non-canonical-path-inventory,
    canonical-cutover-register,
    orphan-object-detection,
    data_pipeline_reconciliation_sports_2026_07_22,
  ]
created: 2026-07-24
resulting_plan:
lib_version:
doc_versions_checked:
audited_scope:
  "asset_group=sports, raw-tick layer only, PROD (-prd-) buckets only, read-only. Primary: market-data-tick-sports-prd
  full manifest read (predicate/column-projected), reuse of the 2026-07-21 whole-corpus orphan sweep (single-walk
  exempt), live GCS delimiter descent (multiple days), machine-oracle sample (20 objects), one parquet content read,
  distinct-value venue census (full manifest vs UAC registries), S4 catalogue grep. Secondary/cross-check only:
  instruments-store-sports-prd (2 targeted queries, not independently four-surface-reconciled). NOT reconciled: candles
  layer, Tier-2 100%-corpus per-datapoint validation, full S1<->S3 join, id-form (G2) canonical-id-builder check."
date: 2026-07-24
auditor: /data-pipeline-reconciliation sports (dispatched sub-agent)
parent_epic: sports_master
severity: P1
---

# /data-pipeline-reconciliation — sports — 2026-07-24 (raw-tick layer)

**Scope**: raw-tick layer only (`--layer candles` explicitly out of scope for this dispatch). PROD buckets only. Tier 1
(in-session, no VM) — interactive mode, stop after this run.

## Phase 0 — resolution gate

### Bucket paths

| kind              | asset_group | resolved bucket                                       | reachable | notes                                                                                                                |
| ----------------- | ----------- | ----------------------------------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------- |
| market-data       | sports      | `market-data-tick-sports-prd-central-element-323112`  | ✅ yes    | **primary bucket for this dispatch** — raw-tick MTDS estate                                                          |
| instruments-store | sports      | `instruments-store-sports-prd-central-element-323112` | ✅ yes    | cross-referenced only (2 targeted queries), to test the F1 hypothesis below — NOT independently reconciled this pass |

Resolved via `resolve_bucket_name(cloud='gcp', kind=..., asset_group='sports', deployment_env='prd')` — keyword-only, no
bucket-name fragment, no inline `gs://`. `GCP_PROJECT_ID=central-element-323112` set in env (the sanctioned, non-tier
env read). Reachability proven by a **non-recursive top-level listing** (`list_blobs(delimiter='/')`), not assumed:

```
market-data-tick-sports-prd-central-element-323112 top-level prefixes:
  _index/  _legacy_migrated_processed/  _legacy_migrated_scripts/  _legacy_migrated_vm_staging/
  _vm_staging/  processed/  raw_tick_data/  scripts/
```

No `-test-` bucket resolved (refusal condition not triggered).

### Index freshness / lock state (read 2026-07-25T00:57–01:11Z)

| bucket                               | `_index/latest.json`                                                                                                                                           | lock state | `_index/phantom_audit_latest.json`                                                                                                                                                                             |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| market-data-tick-sports              | `last_run_at=2026-07-25T00:57:42Z, success=true, verdict=empty, shards_scanned=1, no_op=true` — fresh, healthy, no stall (`consolidator_stall_state.streak=0`) | no lock    | **NOT PRESENT** — declared coverage gap; S3 "phantom" (captured claim, no object) verdict NOT independently checked this pass, distinct from the orphan_real finding below (object, no claim) which IS covered |
| instruments-store-sports (cross-ref) | `last_run_at=2026-07-25T01:10:43Z, success=true, verdict=empty, no_op=true` — fresh                                                                            | no lock    | not checked                                                                                                                                                                                                    |

Both indices report `no_op: true` — i.e. the consolidator found nothing new to fold in from its own per-VM shards at
read time. This is consistent with (and does not contradict) the F1 finding below: if the writer that would populate
`market-data-tick-sports-prd`'s own per-VM shards has stopped emitting them, the consolidator has nothing to consolidate
and correctly reports a healthy no-op — **infrastructure health and data completeness are orthogonal here**; a green
consolidator does not imply a complete manifest.

Also read `_index/audit/*.parquet` (pre-computed sweeps, read per the skill's own instruction to prefer these over
re-deriving): `orphan_sweep_sports.parquet` (2026-07-21T10:13:55Z, 27,348 rows), `legacy_dup_delete_list_sports.parquet`
(2026-07-13, 0 rows — empty), `legacy_unmappable_verify_sports.parquet`, `projected_index_sports_v2.parquet`, two
`projected_sports_*` recovery snapshots, `sports_md_unmappable_verify_2026_06_19.parquet`. The orphan sweep is the ONE
whole-corpus GCS enumerator this session reused (single-walk route #3) rather than re-walking.

### Suppression inputs loaded

- `canonical-cutover-register.md` §2 (sports `require_pipeline_mode` effective-from **2026-05-19**, plus the standing
  BLK-d48acae4 exception for `instruments-store-sports` — not this bucket) and §6 (sports `data_type` case: K0-DECISION
  ruled UPPER 2026-07-18, register states K1 "NOT SHIPPED" — see F4 below for a contradicting code signal).
- `reconciliation-finding-taxonomy.md` §4 accepted-exception list (AE-1 through AE-6) — AE-1 (blank
  `pipeline_mode`/`source`) checked directly against this manifest: **0 rows**, not applicable here (AE-1 concerns
  `instruments-store-sports`).
- `non-canonical-path-inventory.md` sports-scoped rows (items #1, #4, #13) — re-verified in Phase 2 below.

## Phase 1 — four-surface comparison

### Surface 1 (path) — machine oracle

Every real raw-tick sports object in this bucket lives under
`raw_tick_data/by_date/day={D}/pipeline_mode={m}/asset_group=sports/venue={V}/league_id={L}/instrument_type={IT}/data_type={DT}/ticks.parquet`
— confirmed by direct listing (day=2020-06-06, 2026-07-20, 2026-07-21..24). Ran
`unified_api_contracts.canonical_path_violations()` on a 20-object sample drawn from the orphan-sweep population (dates
2021-05-16 through 2026-07-20, multiple venues/leagues):

```
violations w/ require_pipeline_mode=False: 0 / 20
violations w/ require_pipeline_mode=True:  0 / 20
```

**Path structure is canonical (sampled).** Note: this answers the STRUCTURE question only — no per-instrument
filename-stem/id-form check was run this pass (declared coverage gap).

### Surface 2 (content) — spot check

Read one live object in full:
`raw_tick_data/by_date/day=2026-07-24/pipeline_mode=batch_odds_api/asset_group=sports/venue=DRAFTKINGS/league_id=ALLSVENSKAN/instrument_type=ODDS/data_type=TRADES/ticks.parquet`
— 24 rows, real bookmaker prices (`price`, `point`, `outcome_name`), populated `instrument_id` column
(`FOOTBALL:DRAFTKINGS:MATCH_ODDS:ALLSVENSKAN:2026-27:VASTERAAS-ORGRYTE_IS::HOME`, sports' own id grammar, not the
cefi/tradfi grammar). **Not junk, not a placeholder** — this is genuine `orphan_real` per the taxonomy's own row-count>0
test, not a zero-row phantom-adjacent object. Secondary observation (not investigated further, out of scope):
`af_fixture_id=NaN`, `af_fixture_match_status=UNRESOLVED_TEAM_NAME` — a fixture-join miss, unrelated to
canonicalisation.

### Surface 3 (manifest) — F1: the headline finding

**F1 — `orphan_real`, HIGH severity, active and growing.**

The full `market-data-tick-sports-prd` manifest (`_index/availability_index.parquet`, 465,223 rows, 100%
`asset_group=sports`) was read via column-projected `pyarrow.parquet.read_table`. Its **maximum `date` value across
every pipeline_mode is 2026-07-20** — zero rows of any kind for 2026-07-21 through 2026-07-24 (the day this run executed
against):

```
batch_odds_api rows by date, last 6 dates with any rows:
  2026-07-16: 67   2026-07-18: 83   2026-07-19: 42   2026-07-20: 23   (then: nothing)
day=2026-07-21 / 07-22 / 07-23 under pipeline_mode=batch_odds_api/asset_group=sports/: 0 venue prefixes on GCS at all
  (a real 3-day capture gap on the WRITER side too — not just the manifest)
day=2026-07-24: real, populated GCS objects exist (confirmed above) — ZERO matching manifest rows
```

Cross-referenced against the **reused 2026-07-21 whole-corpus orphan sweep**
(`_index/audit/orphan_sweep_sports.parquet`, single-walk-exempt per route #3): **27,348 total `E_orphan_real` objects**
in this bucket, split `raw_tick_data/` **20,443** and `processed/` (candles layer, out of scope) 6,905. The raw-tick
20,443 are **100%** `pipeline_mode=batch_odds_api`, `instrument_type=odds`, split `data_type=trades` (19,246) /
`trades_inplay` (1,197), across 31 bookmaker venues, spanning **2021-05-16 → 2026-07-20**, totaling ~300.6 MB. This is a
**lower bound** — the sweep predates the 07-21→07-24 gap measured live in this pass, so the true current count is
higher.

As a fraction of the on-disk `batch_odds_api` shard population:
`20,443 / (275,164 manifest rows + 20,443 orphans) ≈ 6.9%` of that lane's real shards carry NO manifest row at all —
against the taxonomy's acceptance bar of `orphan_class_E == 0` per asset_group (`reconciliation-finding-taxonomy.md`
§2.1), this fails badly, and per the live-verified day=2026-07-24 sample, **the gap is not historical — it is happening
right now.**

**Critical caveat, found in this same pass — read before treating this as raw data loss.** Cross-checked the ONE live
sample above (`day=2026-07-24, venue=DRAFTKINGS, league_id=ALLSVENSKAN`) against the **sibling**
`instruments-store-sports-prd` manifest (a bucket this dispatch does not otherwise reconcile — see Bucket paths). That
manifest carries a **matching captured row**: 41 `DRAFTKINGS`/`2026-07-24` rows, and **935** total `batch_odds_api` rows
for `2026-07-24` (plus 42/84/1,121 for 07-21/22/23 respectively — the exact days `market-data-tick-sports-prd`'s own
manifest shows zero for). This strongly suggests the underlying data is **not lost or unknown to the system** — it is
tracked, just in a different bucket's manifest than the one this bucket's own consolidator/orphan-sweep tooling (and
this skill's own default S3 resolution, which reads the SAME bucket it resolves) checks against. A pre-existing
2026-07-14 issue (`sports_phantom_audits_reference_not_marketdata_2026_07_14.md`) already documents that sports'
manifest-writer target is architecturally routed to `instruments-store-sports-prd` for the reference domain — this run
adds live 2026-07-24 evidence that the **raw-tick odds/TRADES manifest activity has also fully relocated there**,
leaving `market-data-tick-sports-prd`'s own index a stale/abandoned secondary surface for new writes (while still
correctly receiving the actual parquet bytes). **This was verified for exactly ONE shard, not the full 20,443-object
population** — do not read this as "F1 is fully explained," only as a load-bearing caveat that changes the finding from
probable data loss to a confirmed, quantifiable **cross-bucket S3-routing defect** that makes any
`market-data-tick-sports-prd`-scoped tool (including this skill's own Phase-0 methodology, and the 2026-07-21 orphan
sweep itself) produce a false/misleading orphan signal at scale for sports specifically — still a real, reportable
defect, not a false positive to simply suppress.

### Surface 4 (catalogue)

`configs/data-catalogue.instruments-service.yaml` (`last_updated: 2026-02-06`, `auto_refreshed: null` — the documented
standing staleness condition, reported once per the skill's own instruction) DOES carry a `SPORTS:` section, keyed on
**provider** (`ODDS_API`, `API_FOOTBALL`, `FOOTYSTATS`, …, genesis `2018-01-01`/`2015-01-01`), not on the raw-tick
manifest's actual `venue=` axis (individual bookmakers: `DRAFTKINGS`, `PINNACLE`, …). A grain mismatch, not a missing
entry: a naive S4 lookup at `venue=DRAFTKINGS` grain finds no catalogue key, but the catalogue's own `venue=""`
("current writer shape") and `ODDS_API` rows do put the _provider_ in scope from 2018-01-01. Per
`four-surface-reconciliation-procedure.md` §1's own rule ("never compare S4 at a grain finer than venue/day"), this is
reported as a **declared coverage-gap / grain-mismatch note**, not a fresh finding.

## Phase 1b — distinct-value census (G1)

### F2 — `non_canonical_axis_value`, MEDIUM severity, S3 (manifest column)

Full venue census of the 465,223-row manifest against `VENUES_BY_ASSET_GROUP['sports']` (8 canonical entries:
`ODDS_API`, `PINNACLE`, `BETFAIR`, `BETFAIR_SB_UK`, `BETFAIR_EX_UK`, `BETFAIR_EX_EU`, `DRAFTKINGS`, `FANDUEL`) and
`SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS` (20 entries, `market_data_categories.py`):

| venue                                                                                                                                                          | rows               | status                                                                                                                                                                                                                                                                                                                                                                    |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ODDS_API                                                                                                                                                       | 166,796            | canonical                                                                                                                                                                                                                                                                                                                                                                 |
| **KALSHI**                                                                                                                                                     | **20,785**         | **NOT canonical, NOT accepted** — registered exclusively under `VENUES_BY_ASSET_GROUP['prediction']`; paired with `source=polymarket_clob`/`pipeline_mode=batch_polymarket_clob` (Kalshi ≠ Polymarket — an internal source/venue contradiction); **100% `capture_status=empty_confirmed`, `row_count=0`** (no real data at stake, unlike F1); dates 2020-06-06→2026-05-21 |
| PINNACLE, BETFAIR_*, DRAFTKINGS, FANDUEL                                                                                                                       | 51,969 (combined)  | canonical                                                                                                                                                                                                                                                                                                                                                                 |
| UNIBET, PADDYPOWER, SKYBET, MATCHBOOK, BETONLINEAG, BETRIVERS, CORAL, WILLIAMHILL, BETVICTOR, VIRGINBET, LIVESCOREBET, CASUMO, BETSSON, BOVADA, BETWAY, BETMGM | 154,431 (combined) | accepted-nonconanical (registered ODDS_API fan-out exception)                                                                                                                                                                                                                                                                                                             |
| **SPORT888**                                                                                                                                                   | **13,997**         | **NOT canonical, NOT accepted** — looks like a legitimate unregistered ODDS_API-fanout bookmaker                                                                                                                                                                                                                                                                          |
| **UNIBET_UK**                                                                                                                                                  | **9,423**          | **NOT canonical, NOT accepted** — distinct from registered `UNIBET`; same pattern                                                                                                                                                                                                                                                                                         |
| **LADBROKES_UK**                                                                                                                                               | **8,859**          | **NOT canonical, NOT accepted** — same pattern                                                                                                                                                                                                                                                                                                                            |
| **SMARKETS**                                                                                                                                                   | **4,162**          | **NOT canonical, NOT accepted** — same pattern                                                                                                                                                                                                                                                                                                                            |
| (blank)                                                                                                                                                        | 2,498              | blank sentinel, not counted as a finding                                                                                                                                                                                                                                                                                                                                  |
| **UNIBET_EU**                                                                                                                                                  | **12**             | **NOT canonical, NOT accepted** — same pattern                                                                                                                                                                                                                                                                                                                            |
| **UNKNOWN**                                                                                                                                                    | **8**              | **NOT canonical, NOT accepted** — literal `UNKNOWN` sentinel, immaterial volume                                                                                                                                                                                                                                                                                           |

**Total non-canonical, non-accepted: 57,246 rows (12.3% of the manifest)**, of which KALSHI is 36.3%. The five
non-KALSHI venues (SPORT888, UNIBET_UK, LADBROKES_UK, SMARKETS, UNIBET_EU — 36,453 rows combined) are almost certainly
the same maintenance-gap class the existing 20-entry accepted list already exists to solve — real, legitimate
ODDS_API-fanout bookmakers simply never added to either registry. **KALSHI is categorically different**: it is not an
unregistered bookmaker, it is a **wrong-asset-group venue** physically present in the sports manifest, with an internal
source/venue mismatch, and — because it is 100% `empty_confirmed`/`row_count=0` — it appears to be a sentinel/negative-
result population (someone/something checking "does sports league X have Kalshi-labeled coverage" and recording an
honest empty, mislabeled) rather than real captured betting data. This is very likely a **sibling instance** of the
already-tracked, actively-investigated cross-AG prediction bleed (see below) — but the row counts differ (20,785 here
vs. 11,727 in the other bucket) and were not verified to be the identical rows, so it should be treated as **additional
evidence for that investigation**, not a confirmed duplicate measurement.

## Phase 2 — non-canonical sweep + delete suggestions

### Register re-check (`/codex/02-data/non-canonical-path-inventory.md`)

| register item                                                                                                                | disposition this pass                                                                                                                                                                                                                                                   |
| ---------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| #1 — 15 legacy flat-named buckets                                                                                            | N/A to this bucket (already-deleted names)                                                                                                                                                                                                                              |
| #4 — `market-data-tick-sports-prd-{pid}/scripts/` + `_legacy_migrated_scripts/scripts/` (executable Python in a data bucket) | **RE-CONFIRMED PRESENT** — `scripts/fetch_missing_odds.py`, `scripts/oddspapi_historical_backfill.py`, `scripts/oddspapi_runner.py` still there. Disposition unchanged: `unknown` — VM-bootstrap-reference check still outside the grep corpus, not resolved this pass. |
| #13 — `market-data-tick-sports-prd-{pid}/processed/` vs `processed_candles/` naming                                          | **RE-CONFIRMED PRESENT** (`processed/`, `_legacy_migrated_processed/` both exist; no `processed_candles/`). This is a **candles-layer** concern — out of scope for this raw-tick dispatch; not investigated further.                                                    |

Also present, not previously registered but low-priority / non-data (class `non_data`, INFO, never delete-eligible per
taxonomy §2.1): `_vm_staging/` (tarballs, launch scripts — 6 objects + 6 sub-prefixes), `_legacy_migrated_vm_staging/`
(empty at top level, one child prefix). Not added to the register — these are operational artifacts, not data-path
non-canonicality, and the register's own scope is GCS **data** locations.

**No new non-canonical GCS _location_ (prefix/directory) found this pass** — F1 and F2 above are S3 (manifest)
content/coverage disagreements, not new non-canonical paths. **No register-patch stanza needed.**

### Delete suggestions

**None.** No candidate this pass carries the five-part proof (`gcs-and-manifest-delete-safety-protocol.md` §1) — this
was a read-focused reconciliation pass; no twin-resolution, content-verify, or writer/reader grep-then-READ was run
against any candidate legacy/duplicate location. Register item #4's disposition remains `unknown` by default.

## Suppressed (accepted exceptions)

- AE-1 (sports blank `pipeline_mode`/`source`, `instruments-store-sports` exception) — checked directly against **this**
  manifest: **0 rows blank**, not applicable here, correctly not suppressed-and-reported as it doesn't occur.
- Sports `data_type` casing (K0-DECISION UPPER target, `migration_pending` per `canonical-cutover-register.md` §6) —
  measured, not flagged: `TRADES` 275,136 / `trades` 22,084 (post-K1-partial-ship split, see F4).

## F3 — this skill's own governing codex is measurably wrong about the bucket it resolves for sports raw-tick

`four-surface-reconciliation-procedure.md` §4.2 states: _"every sports object lives under `sports_reference/`"_ and
_"the oracle does NOT cover sports."_ §6 and this skill's own §3d hazard table repeat: _"sports — No `asset_group=` key
at all — the tree is `sports_reference/by_date/day={D}/pipeline_mode={m}_{s}/entity={E}/league={L}/`."_

**Directly verified against the actual bucket this dispatch's own Phase-0 step resolves**
(`market-data-tick-sports-prd`, `kind='market-data'`): `sports_reference/` has **ZERO objects and ZERO child prefixes**
there. Every real raw-tick object instead lives under the **standard**
`raw_tick_data/by_date/day={D}/pipeline_mode={m}/asset_group=sports/venue={V}/league_id={L}/instrument_type={IT}/data_type={DT}/ticks.parquet`
grammar — which **does** carry an `asset_group=sports` key and **is** covered by the standard oracle (0 violations on a
20-object sample, both `require_pipeline_mode` settings — see Phase 1 §Surface 1 above).

Root cause: `sports_reference/` (and its `entity=`/oracle-exempt description) is real, but it lives in a **different
bucket** — `instruments-store-sports-{env}-{project_id}` (`SPORTS_BUCKET_TEMPLATE`,
`unified_api_contracts/canonical/domain/sports/gcs_paths.py:149`), which this raw-tick dispatch never resolves. The
codex conflates the two buckets' layouts into one "sports raw-tick" description. Any future agent who trusts §4.2/§6
literally for a `market-data-tick-sports-prd` reconciliation will (a) skip running the oracle when it should be run, and
(b) dispatch to `candidate_parquet_paths()`, which returns paths that don't exist in this bucket at all — exactly the
kind of wrong-playbook risk that likely contributed to F1 going unnoticed by generic tooling.

This is closely related to, but distinct from, the pre-existing
`sports_phantom_audits_reference_not_marketdata_2026_07_14.md` issue (which is scoped to the phantom AUDITOR's bucket
routing). F3 is scoped to **this reconciliation skill's own codex SSOT** being wrong about which bucket its §4.2/§6
sports description applies to — filed as its own small issue doc (see below) rather than folded into the phantom-audit
issue, since the fix target (the codex file) is different.

## Formulas named

- `reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)`, `empty_confirmed` EXCLUDED
  (`honest-coverage-model.md`, CK3-certified). For `market-data-tick-sports-prd`: `captured=443,303`,
  `attempted_failed=0`, `expected_unattempted=0` → **formula collapses to 100.0%**. **This number is DEGENERATE, not
  healthy** — it is a lower bound that is structurally blind to F1's 20,443+ orphan objects (they carry no manifest row
  at all, so they cannot appear in ANY manifest-keyed formula's numerator or denominator). Do not quote 100% without
  this caveat.
- F2's 12.3% = `57,246 / 465,223` (non-canonical-non-accepted venue rows / total manifest rows).
- F1's 6.9% = `20,443 / (275,164 + 20,443)` (orphan raw objects / (manifest-covered + orphan) real shards for
  `pipeline_mode=batch_odds_api`), a lower bound (pre-dates the live 07-21→07-24 gap).

## Coverage gaps (declared, not silently omitted)

1. **`instruments-store-sports-prd` only spot-checked** (2 targeted queries to test F1's cross-bucket hypothesis) — not
   independently four-surface-reconciled; out of THIS dispatch's raw-tick/`market-data` scope by design.
2. **`--layer candles` not run** — explicitly out of scope per dispatch instructions; `processed/` tree in this same
   bucket untouched beyond the register re-check above.
3. **No Tier-2 (VM, 100%-corpus) per-datapoint validation dispatched** — Tier-1 only (interactive mode, no VM launched
   this pass).
4. **`_index/phantom_audit_latest.json` absent for this bucket** — S3 "phantom" verdict (captured claim, no object) NOT
   independently checked; distinct from F1 (object, no claim), which IS covered.
5. **id-form (G2) canonical-id-builder check not run** — S2 content was read (one object) and its `instrument_id` column
   format observed, but not run through `build_canonical_instrument_id` for byte-equality.
6. **F1's cross-bucket cross-check verified only ONE shard**, not the full 20,443-object orphan population — the "likely
   not real data loss" caveat is a hypothesis with one confirming data point, not a proof.
7. **Full 465,223-row S1↔S3 join not performed** — only a 20-object oracle sample plus the reused 2026-07-21
   whole-corpus orphan sweep.

## Big-picture verdict

**Sports raw-tick (`market-data-tick-sports-prd`) is NOT 100% canonical**, and not primarily on the axis this skill's
own codex would have led an auditor to expect (casing/`pipeline_mode` structure — both clean, sampled). The two real,
measured gaps are: **(F1)** an active, currently-growing manifest-coverage gap in this bucket's own index (0 new rows
since 2026-07-20 against daily real writes, 20,443+ pre-existing orphan objects) — caveated by same-pass evidence that
the data is very likely tracked in a sibling bucket's manifest instead, making this a confirmed cross-bucket S3-routing
defect rather than confirmed data loss; and **(F2)** a 12.3% venue-vocabulary drift, the largest slice of which (KALSHI,
36.3% of the drift) is a wrong-asset-group venue tied to an already-open P0 cross-AG bleed investigation elsewhere in
this codebase. Additionally **(F3)** the reconciliation skill's own SSOT misdescribes which bucket the sports "no oracle
coverage" / "no `asset_group=` key" characterization applies to — a documentation-accuracy defect in the very playbook
this run followed. No new non-canonical GCS location was found; no delete suggestions (none had the required 5-part
proof this pass).

## Cross-references filed this pass

- **New issue** (F3, genuinely new ground — no existing doc targets the reconciliation skill's own codex accuracy):
  `plans/archive/issues/reconciliation_skill_sports_raw_tick_ssot_wrong_bucket_2026_07_24.md` (resolved 2026-07-25)
- **Addendum appended** to `plans/active/issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md`
  (F1 — answers that issue's open "is the pipeline dormant" question: no, it is writing real data; the manifest signal
  it used was reading the architecturally non-authoritative bucket)
- **Addendum appended** to
  `plans/archive/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` (F2's KALSHI slice —
  answers that issue's own explicitly-flagged-but-unchecked "also check the market-data(tick)/sports manifest for the
  same bleed" item)
