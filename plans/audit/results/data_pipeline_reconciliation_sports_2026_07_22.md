---
doc_type: audit-result
title: "Data-pipeline reconciliation — sports (2026-07-22)"
summary: >-
  Tier-1 (in-session, no VM) four-surface canonicalisation reconciliation of asset_group=sports, raw-tick layer only,
  over PROD buckets (read-only). Both prod buckets (tick-data, instruments-store) resolve and are reachable;
  instruments-store consolidator was actively locked at read time (results are a lower bound). Machine oracle finds BOTH
  canonical and non-canonical-cased instrument_type/data_type paths structurally CANONICAL (casing is a deliberately
  unenforced migration_pending axis). Live GCS listing confirms the K1 live-writer casing gap
  (sports_consolidated_closeout_2026_07_19.md) is an ONGOING leak, not settled history — same-day objects exist in both
  cases side by side. Distinct-value census: 275,136 ODDS/TRADES rows (this session's relocation) vs 1,337,763 still
  lowercase odds/trades (K2 scope, live-measured and narrower than the plan's earlier ~1.8M estimate). Found 6,110
  residual phantom soccer_* league_id manifest rows (GCS objects already deleted; already-tracked, not new). Cross-AG
  bleed re-confirmed at 11,727 rows, growth-halt not yet confirmed. No new non-canonical location found; the
  reconciliation's main value was catching that an issue doc filed earlier the same session duplicated the
  already-tracked K1 todo (corrected + cross-linked). No delete suggestion crosses the human-only prod-bucket hard stop.
  Declared coverage gaps: candles layer, reference-data entity= tree, Tier-2 100%-corpus validation all NOT run this
  pass.
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
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, four-surface, sports, manifest, casing, k1, cross-ag-bleed, league-id]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    gcs-and-manifest-delete-safety-protocol,
    non-canonical-path-inventory,
    canonical-cutover-register,
    orphan-object-detection,
  ]
created: 2026-07-22
resulting_plan:
lib_version:
doc_versions_checked:
audited_scope:
  "asset_group=sports, raw-tick layer only, PROD (-prd-) buckets only, read-only; sample = tick-data manifest slim
  column-projected read (date/league_id/instrument_type/data_type/venue/capture_status) + machine oracle on 2 live path
  samples (canonical + non-canonical-cased) + live GCS delimiter listing of one day's objects + reuse of this same
  session's manifest-swap verify_swap() re-derivation + reuse of this session's cross-AG bleed measurement. NOT
  reconciled: candles layer, reference-data entity=/league= tree, features/catalogue (surface 4), whole-corpus orphan
  walk, Tier-2 100%-corpus per-datapoint id/schema validation."
date: 2026-07-22
auditor: /data-pipeline-reconciliation sports
parent_epic: sports_master
severity: P1
---

# /data-pipeline-reconciliation — sports — 2026-07-22

**Scope**: raw-tick layer only (`--layer candles` NOT run this pass — declared coverage gap below). PROD buckets only.
Tier 1 (in-session, no VM) — no Tier-2 100%-corpus per-datapoint validation dispatched this pass.

**Context**: this reconciliation ran at the end of a long same-day session that executed the league_id relocation's
manifest-swap (`mtds@250d377b`), a full MDPS `odds_horizon_bucket` reprocess (2,236 days), and a coverage-registry
refresh (`uac@8e8d2e5b`) — see `plans/active/sports_master_closeout_2026_07_21.md` Progress Log for the full trail.
Several of the findings below are direct, live confirmations of gaps already surfaced during that work.

## Bucket paths

| kind              | resolved bucket                                       | reachable | notes                                          |
| ----------------- | ----------------------------------------------------- | --------- | ---------------------------------------------- |
| tick-data (raw)   | `market-data-tick-sports-prd-central-element-323112`  | ✅ yes    | odds ticks + MDPS `odds_horizon_bucket` output |
| instruments-store | `instruments-store-sports-prd-central-element-323112` | ✅ yes    | canonical sports manifest + reference data     |

Resolved via `resolve_bucket_name(cloud="gcp", kind=..., asset_group="sports")` — no bucket-name fragments, no inline
`gs://`. `GCP_PROJECT_ID=central-element-323112` set in env (the sanctioned, non-tier env read).

## Index freshness / lock state (Phase 0d — read at 2026-07-22T16:56Z)

| bucket            | `_index/latest.json`                                                                        | lock state                                                                                                                                                                                                                 |
| ----------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| tick-data         | `last_run_at=2026-07-22T16:55:47Z, success=true, no_op=true` — fresh, incremental, healthy  | no lock                                                                                                                                                                                                                    |
| instruments-store | `last_run_at=2026-07-22T16:56:34Z, success=true, verdict=empty, error_reason="locke[d]..."` | **`consolidator.lock` HELD** at read time (`started_at=2026-07-22T16:55:41Z`, instance `1-4cb2e920`) — almost certainly the consolidator re-deriving after this session's MDPS-reprocess manifest write (168,886 new rows) |

**Per § 2d: the instruments-store surface-3 verdict below is a lower bound** — read against a bucket whose consolidator
was actively running. `_index/phantom_audit_latest.json` on instruments-store is **stale**: `generated_at=2026-07-14`,
`phantom_count=721,154` — dated BEFORE the 2026-07-21 pre-floor wipe (649,643 objects) and this session's manifest-swap

- MDPS reprocess, so that number is **not trustworthy today** and is reported as historical only, not current.

## Phase 1 — four-surface comparison (odds/trades raw-tick shape, the corpus this session's work targeted)

**Surface 1 (oracle path structure)** —
`unified_api_contracts.canonical_path_violations(path, require_pipeline_mode=True)` (register: sports
`require_pipeline_mode` effective-from 2026-05-19) returns **0 violations** for BOTH a canonical
(`instrument_type=ODDS/data_type=TRADES`) and a non-canonical-cased (`instrument_type=odds/data_type=trades`) live path
sampled from `day=2026-07-20` — **by design**: the oracle does not currently enforce sports
`instrument_type`/`data_type` casing (an open `migration_pending` axis per `canonical-cutover-register.md` § 6, K1 not
shipped). So "0 violations" here answers "is the path skeleton well-formed", not "is casing canonical" — stated
explicitly per the skill's own warning against conflating the two.

**Live-confirmed**: the SAME `(day=2026-07-20, venue=BETFAIR_EX_EU, league_id=ALLSVENSKAN)` cell carries BOTH the
canonical and non-canonical-cased object side by side on disk — direct GCS-listing proof (not inferred) that the K1
live-writer gap is producing non-canonical objects on dates well after this session's relocation, i.e. it is an ongoing
leak, not settled history.

**Distinct-value census — `instrument_type`/`data_type` casing (odds/trades shape, live manifest read, 2026-07-22)**:

| value pair        | rows      | source                                                              |
| ----------------- | --------- | ------------------------------------------------------------------- |
| `ODDS` / `TRADES` | 275,136   | this session's league_id-relocation manifest-swap ADD (exact match) |
| `odds` / `trades` | 1,337,763 | historical + ONGOING daily writes (K1/K2 scope, not yet migrated)   |

This is a precise, live-measured scope for **K2** (`sports_consolidated_closeout_2026_07_19.md` Track C) restricted to
the odds/trades family specifically — narrower and more current than that plan's earlier ~1.8M all-`trades` estimate
(which spans instrument_types beyond odds).

**league_id — RESIDUAL non-canonical rows found, matches an ALREADY-OPEN todo, not a new finding**: within the
odds/trades shape, **6,110 rows** still carry a raw lowercase `soccer_*` league_id (e.g. `soccer_epl`: 341 rows,
`soccer_spain_la_liga`: 336, ... — full long-tail), all dated **2025-07-31 .. 2025-12-31**. This is the
`mtds_t2_6_league_case_duplicate_population` phantom-row population named in `sports_master_closeout_2026_07_21.md`'s
still-open todo ("Prune the twin-delete phantom manifest rows" — the underlying GCS objects were already
crc-verified-identical to their `SOCCER_*` twins and DELETED; these are now manifest-only phantom rows). **Progress
since that todo was last measured**: it cited 7,295 rows; live count today is 6,110 — ~1,185 were incidentally cleaned
by this session's relocation manifest-swap CAS-remove pass, but the todo's own full prune did not run and remains
genuinely open. Elsewhere in the manifest, league_id is fully canonical for the odds/trades shape (0 other non-uppercase
values found beyond this known population).

**Cross-AG bleed** (`asset_group=prediction` rows physically in the `instruments-store-sports-prd` index) — re-measured
this session (see `sports_master_closeout_2026_07_21.md` Progress Log): **11,727 rows**, growth halted as of the writer
fix (`mtds@07aa4271`) landing — newest bleed row predates the fix's push time; full confirmation needs one more daily
capture cycle post-fix (not yet observed). Cleanup of the already-accumulated rows is a separate open todo, not
attempted this pass (read-only reconciliation).

**Surface 3 (manifest) vs Surface 1 (path) for the relocated cells specifically**: independently re-verified this
session via the manifest-swap tool's own `verify_swap()` (post-fix) — 275,136/275,136 canonical ADD rows present with
byte-exact `row_count` matching the relocation's own content-verified totals, 0 missing, 0 mismatched. (The tool's
initial run reported a false `stale_remaining=162,137`, root-caused and fixed same-session — `mtds@250d377b` — see the
master plan's Progress Log for the full analysis; not re-litigated here.)

**Surface 4 (catalogue)** — not audited this pass (declared coverage gap below).

## Phase 2 — non-canonical sweep

Register (`codex/02-data/non-canonical-path-inventory.md`) re-check for sports-scoped entries: no new non-canonical
location found beyond what's already tracked (the K1 casing axis + the 6,110-row phantom population above, both
already-registered/tracked, not new register entries).

### Delete / cleanup suggestions

| candidate                                                            | disposition                                                                   | why                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| -------------------------------------------------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Old non-canonical relocated GCS objects (lowercase league_id/casing) | `no-migrate-first`                                                            | Part 3 (no live writer) FAILS — K1 unshipped, new non-canonical objects land daily. Full 5-part-proof checklist already published in `sports_master_closeout_2026_07_21.md`. Prod-bucket delete is human-only regardless.                                                                                                                                                                                                                                                                                                                                |
| 6,110 phantom `soccer_*` manifest rows (GCS objects already deleted) | `yes-twin-confirmed`-equivalent, but **manifest-row prune, not a GCS delete** | Objects gone (Part 1 twin absent by design — this IS the delete-already-happened case), content moot (Part 2 n/a), no writer targets this dead population (Part 3 pass — these dates are 2025, no live writer touches them), no reader depends on a phantom row (Part 4 pass). **Not gated by the prod-bucket-delete hard stop** (no GCS object touched) — but IS gated by the workspace's own "never hand-edit the manifest index" rule; must go through the sanctioned GCS-walk rebuild route already named in the open todo, not a session hand-edit. |

## Suppressed (accepted exceptions)

- Sports `instrument_type`/`data_type` casing (C0/K0-DECISION axis) — `migration_pending`, compared per the register's
  own framing, not flagged as a fresh non-canonical finding (only reported as a precise census + live-leak evidence).
- The 19,274-row `instruments-store-sports` operator-accepted historical exception (`canonical-cutover-register.md`
  line 114) — not re-measured this pass, cited as still-standing per the register.

## Coverage gaps (declared, not silently omitted)

1. **`--layer candles` not run this pass** — MDPS `processed/` sports tree not audited.
2. **Reference-data tree (`sports_reference/by_date/`, `entity=`/`league=` hive keys) not audited** — this pass scoped
   to the raw-tick odds/trades corpus this session's work targeted; the reference/fixtures estate (its own known gaps:
   the `FIXTURES` umbrella `data_type` per `canonical-cutover-register.md` § 6, C1 in the consolidated plan) needs its
   own pass.
3. **No Tier-2 (VM, 100%-corpus) per-datapoint id/schema validation dispatched** — Tier-1 sampled/live-spot-checked
   only, as documented above.
4. **Distinct-value census scoped to `league_id`/`instrument_type`/`data_type`** — `venue`/`chain` axes not swept this
   pass.
5. **Cross-AG bleed cleanup not verified halted** — one more daily capture cycle needed post-writer-fix before that
   claim can be made with confidence (see above).

## Formulas named

- "Odds/trades shape" = `instrument_type.lower()=='odds' AND data_type.lower()=='trades'` on the live
  `instruments-store-sports-prd` `_index/availability_index.parquet` (slim column-projected read: `date`, `league_id`,
  `instrument_type`, `data_type`, `venue`, `capture_status`).
- All row counts above are **live snapshots at 2026-07-22T16:5x Z**, taken while the instruments-store consolidator was
  actively re-deriving (see Index freshness) — treat as a lower bound / point-in-time, not a settled final count.

## Big-picture verdict

Sports raw-tick odds/trades is **NOT YET fully canonical**, on ONE known, already-tracked, actively-in-progress axis
(`instrument_type`/`data_type` casing, K1/K2) — everything else this pass checked (league_id, the relocation's own
manifest-swap correctness, oracle path structure) is clean or has a precise, bounded, already-tracked residual. No new
non-canonical location was discovered. The single actionable next step this reconciliation surfaces is: ship K1 (with
its documented MDPS-scanner dual-accept pre-step), per
`plans/active/issues/sports_live_writer_instrument_type_casing_never_fixed_2026_07_22.md` +
`sports_consolidated_closeout_2026_07_19.md` Track C.
