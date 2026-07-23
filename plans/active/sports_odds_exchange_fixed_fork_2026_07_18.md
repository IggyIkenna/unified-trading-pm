---
doc_type: plan
title: Sports odds instrument_type fork — EXCHANGE_ODDS / FIXED_ODDS (UAC contract fork + GCS migration)
summary:
  Operator ruled 2026-07-18 to fork the sports `odds` instrument_type into EXCHANGE_ODDS (peer-to-peer commission
  exchanges) vs FIXED_ODDS (sportsbooks). `odds` is a LIVE UAC contract-registry key + physical GCS hive partition
  (561,260 rows) with zero shard/display consumers — so this is a real UAC contract fork + GCS object migration, done in
  the only safe order (contracts → dual-read → GCS move → dependency_checker → manifest LAST), NOT a manifest rename.
  Manifest-first is the corrupting order that cost tradfi its CME counts. Requires a pre-drain of the sports writers
  because `odds` is written live.
status: superseded
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-api-contracts, instruments-service, market-data-processing-service, unified-trading-library]
scope: [engineer]
tags: [sports, canonicalisation, instrument-type, uac-contract-fork, gcs-migration, odds]
related: [/plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md]
created: 2026-07-18
last_updated: 2026-07-23
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source:
  "data_status_page_ux_and_canonicalisation_2026_07_16.md P4-A side-discovery D1 (operator ruling 2026-07-18: FORK)"
locked_by:
locked_since:
supersedes:
superseded_by: sports_consolidated_closeout_2026_07_19.md
---

> **🟡 SUPERSEDED 2026-07-23 — folded into `sports_consolidated_closeout_2026_07_19.md`.** This plan was one of 4
> fold-in plans the operator directed to archive in this batch (`sports_manifest_canonicalisation_2026_06_01`,
> `sports_pipeline_to_100pct_golden_window_first_2026_06_27`, `sports_odds_exchange_fixed_fork_2026_07_18` (this doc),
> `sports_p2_history_apifootball_2015_to_present_2026_06_27`). **Every todo below was still open (0/10 done)** at
> archival time, including the P0 `[OPERATOR]` block on the ambiguous venue→class mapping (bare
> `BETFAIR`/`ODDS_API`/`PINNACLE`), which was BLOCKED-OPERATOR-DECISION and never confirmed. All of it — the operator
> ruling, the venue→class mapping (evidenced poles + the 3 unconfirmed edges), the strict
> contracts→dual-read→GCS-move→dependency_checker→manifest-last ordering, and every one of the 10 todos — has been
> extracted and pulled into `sports_consolidated_closeout_2026_07_19.md` (Track C's "EXCHANGE_ODDS vs FIXED_ODDS fork"
> todo, expanded with this plan's full detail). **Do not pick up further work from this file** — read/update the
> closeout instead; this file is kept only as the historical record of the original ruling + investigation.

# Sports odds instrument_type fork — EXCHANGE_ODDS / FIXED_ODDS

**Operator ruling (2026-07-18):** fork sports `odds` into `EXCHANGE_ODDS` vs `FIXED_ODDS` for real (D1 = option B), with
the venue→class mapping "by mechanism + operator confirms the true edges" (the ambiguous middle will NOT be guessed).

## Context (why this is a contract fork, not a rename)

`odds` is NOT a UAC `InstrumentType` member, but the 2026-07-17 investigation (`wf_a5766faa`, survived 3 adversarial
lenses, 0 refutations) found it is **a live UAC `CONTRACT_REGISTRY` key** (`_sports_prediction_contracts.py`, resolved
by `contracts.py::lookup_contract` on `(asset_group, instrument_type, data_type)`) **AND a physical GCS hive partition**
(53,698 of the first 60,000 sampled objects under `instrument_type=odds/`, still being written). It has **zero shard
consumers and zero display consumers** for sports
(`SHARD_AXIS_MATRIX[(instruments-service, SPORTS)] = ("data_type","league_id")`). `EXCHANGE_ODDS`/`FIXED_ODDS` are
already live enum members (`betfair.py:287` constructs `EXCHANGE_ODDS`; UTL `_derive_instrument_id.py:85` maps
`("sports","odds")→EXCHANGE_ODDS`). Genuinely sports = `odds` **561,260** rows. (The `prediction_market`/`prediction`
rows in the sports index are a separate bucket-ROUTING bug, NOT this; `SPORT` 16 rows = D2, owned by another agent per
operator 2026-07-18 — out of scope here.)

**Migration-order lesson (HARD):** manifest-first is the corrupting order — it created manifest↔disk↔registry divergence
that cost tradfi its CME 2026-06-28 counts (repaired @bd115230). This plan lands manifest LAST.

## Venue → class mapping (2026-07-18 ruling: by mechanism + operator confirms edges)

- **EXCHANGE_ODDS** (peer-to-peer, commission model — evidenced): `BETFAIR_EX_UK` (17,049), `BETFAIR_EX_EU` (16,201),
  `SMARKETS` (8,200), `MATCHBOOK` (28,616 — corroborated by UAC `_SNAPSHOT_VENUES` + `traded_volume`
  `provided_by_venues={'BETFAIR'}`, exchange-only).
- **FIXED_ODDS** (sportsbook — by mechanism): `BETFAIR_SB_UK`, `BETMGM`, `PINNACLE` (32,616 — sportsbook by mechanism,
  though UAC models it `PINNACLE_AS_LINE` in `_SNAPSHOT_VENUES` → **operator-confirm**).
- **OPERATOR-CONFIRM edges** (task T0 below, do NOT guess): bare `BETFAIR` (33 rows), `ODDS_API` (33 — an aggregator,
  fits neither member), `PINNACLE` (confirm FIXED_ODDS vs a PINNACLE_AS_LINE special case).

## Codex SSOTs (read before touching)

- `/codex/02-data/availability-manifest-and-data-status.md` — shard-atom / manifest write discipline (manifest LAST).
- `/codex/06-coding-standards/data-status-endpoint-contract.md` — formula-consistency contract for coverage.
- `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — IS as reference-data SSOT; venue lists = UAC data.
- The 2026-06-28 tradfi CME manifest-first corruption (repaired @bd115230) — the anti-pattern this plan avoids.

## Todos (strict order — this is a DAG, manifest LAST)

- [ ] [OPERATOR] P0. **Confirm the ambiguous venue→class mapping** (bare `BETFAIR`, `ODDS_API`, `PINNACLE`) before any
      code lands. BLOCKED-OPERATOR-DECISION until confirmed. The evidenced poles (above) may proceed to design.
- [ ] [DATA] P0. **Pre-drain the sports odds writers** — `odds` is written live (latest `written_at` 2026-07-17); stop
      all sports odds-writing jobs (both clouds) and snapshot before any GCS object move, so the corpus is frozen for
      the migration (same drain discipline as any GCS cutover).
- [ ] [DATA] P1. **UAC contracts first** — add `EXCHANGE_ODDS`/`FIXED_ODDS` contract entries to
      `_sports_prediction_contracts.py` keyed on the new instrument_types + the confirmed venue→class map; keep the
      existing `odds` contract entry live (do not delete yet — dual-read next).
- [ ] [DATA] P1. **Dual-read in `lookup_contract`** — resolve BOTH the legacy `odds` key and the new
      `EXCHANGE_ODDS`/`FIXED_ODDS` keys during the migration window, so readers never miss a row mid-move. UAC unit test
      for both paths.
- [ ] [DATA] P1. **GCS object move** — migrate `instrument_type=odds/` objects to `instrument_type=exchange_odds/` /
      `instrument_type=fixed_odds/` per the venue→class map, via UTL `gcs_copy_object`/`gcs_delete_object` (never
      subprocess gsutil); verify-before-write (snapshot → move → independent re-read count), idempotent + resumable.
- [ ] [DATA] P1. **MDPS `dependency_checker` hive-token search** — update the hive-token matcher so it recognises the
      new `instrument_type` partitions (search for every consumer of the `odds` hive token; none should be orphaned).
- [ ] [DATA] P1. **Manifest LAST** — reconcile the availability manifest to the new instrument_type partitions only
      AFTER the GCS move + dual-read are proven; verify the shard atom is identical across writer/manifest/status/gate.
- [ ] [DATA] P2. **Cut the writers over** — point the live sports odds writers at the new instrument_types (per venue),
      un-drain, and confirm new captures land under `exchange_odds`/`fixed_odds`.
- [ ] [DATA] P2. **Retire the legacy `odds` contract + dual-read** once no object/manifest row remains under `odds` and
      a full corpus re-read confirms parity.
- [ ] [REVIEW] P2. **Post-phase codex audit** — update `availability-manifest-and-data-status.md` + the sports
      canonical-naming doc with the new instrument_types + the migration order; confirm no plan↔codex drift.

## Progress Log

- **2026-07-18** — Authored from the data-status round-3 side-discovery D1 after the operator ruled FORK (not
  close-as-not-a-defect). Human plan (operator-driven). `SPORT` (D2, 16 rows) explicitly excluded — another agent owns
  it per operator.
