---
doc_type: issue
title:
  Sports phantom audit targets the REFERENCE manifest (instruments-store-sports), not market-data — inconsistent with
  every other AG, splits phantom/reprobe across two cockpit cards, and reports an unverified 44% (721,154) phantom rate
summary:
  'Discovered 2026-07-14 while running phantom + reprobe audits across all consolidators to populate the cockpit audit
  lines. For cefi/defi/tradfi/prediction the phantom reconciler audits the MARKET-DATA manifest (market-data-tick-<ag>),
  the same bucket reprobe audits — so both audit lines land on one card. Sports is the sole exception: phantom''s
  `_BUCKET_KIND_MAP["sports"] = ("instruments-store", "sports")` points it at the REFERENCE manifest
  (instruments-store-sports / sports_reference), while reprobe (via `_dp_common.manifest_bucket`) audits
  market-data-tick-sports. Result: sports phantom lights the `instruments-sports` card (721,154 phantoms) and reprobe
  lights the separate `market-data-sports` card (0 disagreements) — the two signals never appear together, and there is
  NO market-data phantom audit for sports at all. The sports phantom audit is internally CONSISTENT (its `_audit_sports`
  path templates match the instruments-store sports_reference layout — proven by 923,942 real captures matched), so this
  is NOT a wrong-bucket bug and the naive one-line map flip would BREAK it (market-data-tick-sports has no
  `sports_reference/...` paths → ~100% false-flag). The 44% phantom rate (721,154 of 1,645,101 captured) on the
  reference manifest is UNVERIFIED — it may be a genuine large sports-reference phantom problem or a stale path-template
  gap. Operator decision 2026-07-14: leave code as-is, document only.'
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service, e2e-testing, deployment-api, deployment-ui]
scope: [engineer, admin]
tags:
  [
    sports,
    phantom-audit,
    reprobe,
    manifest,
    bucket-resolution,
    data-correctness,
    cockpit,
    consolidator,
    reference-data,
    unverified-count,
  ]
related:
  [
    consolidator_throughput_backlog_monitor_2026_07_09.md,
    ../../../codex/05-infrastructure/manifest-consolidator-ssot.md,
    ../../../codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
  ]
created: 2026-07-14
parent_epic: observability_master
priority: P2
source:
  Interactive session 2026-07-14 (slot-3·hk) — running phantom+reprobe across all consolidators to populate cockpit
  audit lines; discovered the sports split when the two signals landed on different cards.
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
assigned_role: infra
drift_direction: advance-code
depends_on: []
---

# Sports phantom audit targets the reference manifest, not market-data

## What was found

While populating the cockpit consolidator audit lines (the `phantoms N` / `reprobe N disagree` rows added by
`consolidator_throughput_backlog_monitor_2026_07_09.md`), I ran the phantom reconciler and the empty re-probe against
all data-capture asset groups. Every group's two signals landed on one card **except sports**, whose phantom and reprobe
landed on two different cards.

### Root cause — the two audits resolve different sports buckets

| audit                                                                     | resolver                                                       | bucket                           | cockpit card         |
| ------------------------------------------------------------------------- | -------------------------------------------------------------- | -------------------------------- | -------------------- |
| phantom (`reconcile_phantom_manifest_rows_all.py`)                        | `_BUCKET_KIND_MAP["sports"] = ("instruments-store", "sports")` | `instruments-store-sports-prd-…` | `instruments-sports` |
| reprobe (`reprobe_new_empty_confirmed.py` → `_dp_common.manifest_bucket`) | market-data                                                    | `market-data-tick-sports-prd-…`  | `market-data-sports` |

For cefi/defi/tradfi/prediction the phantom map uses `("market-data", <ag>)`, i.e. the SAME `market-data-tick-<ag>`
bucket reprobe audits — so both lines share a card. Sports is the only AG mapped to `instruments-store`.

### The buckets hold genuinely different data (verified by reading both indexes 2026-07-14)

- `market-data-tick-sports` (1.96M rows) — market data: `trades` (1.79M), `odds`, `ODDS`, `odds_horizon_bucket`; real
  betting venues (PINNACLE, BETFAIR, KALSHI, POLYMARKET…). This is the true market-data analog of
  `market-data-tick-{cefi,defi,tradfi}`.
- `instruments-store-sports` (5.76M rows) — reference/enrichment data: `TEAMS`, `INJURIES`, `FIXTURES`, `STANDINGS`,
  `XG`, `PLAYER_VALUES`, `PREDICTIONS`; venue mostly blank (4.95M rows). This is the sports instrument universe, owned
  by instruments-service.

Every AG has BOTH bucket types (`market-data-tick-<ag>` + `instruments-store-<ag>`); sports is not structurally special.

## Why this is NOT a simple one-line fix

`_audit_sports` (`reconcile_phantom_manifest_rows_all.py:283`) probes `sports_reference/by_date/day={D}/…` and
`sports_reference/{folder}/{folder}.parquet` paths via `unified_api_contracts.sports.candidate_parquet_paths`. Those
paths MATCH the `instruments-store-sports` layout — confirmed by the audit finding **923,942 real captures** (parquet
present) alongside the 721,154 phantoms. So the current sports phantom audit is internally consistent: correct bucket +
correct path templates for the reference manifest.

Flipping `_BUCKET_KIND_MAP["sports"]` to `("market-data", "sports")` (the naive "make it like the others" fix) would
point the same `_audit_sports` at `market-data-tick-sports`, where no `sports_reference/…` paths exist → it would
false-flag ~100% of captured rows as phantom. **Do not apply that change.**

The real gap is that **no market-data phantom audit exists for sports** — filling it means routing sports market-data
through `_audit_generic` (market-data path templates) against `market-data-tick-sports`, a genuine feature addition, not
a config flip.

## Open sub-items

1. **Design inconsistency (tracked, not urgent):** sports phantom audits reference data; every other AG's phantom audits
   market-data. `market-data-sports` therefore has no phantom line and `instruments-sports` has no reprobe line. Full
   symmetry would require (a) a market-data sports phantom path via `_audit_generic`, and separately (b) reprobe never
   audits any instruments-store manifest, so the reference side is phantom-only by design.
2. **Unverified 721,154 reference phantoms (data-correctness, needs a look before any `--apply`):** 44% of captured rows
   in `instruments-store-sports` have no parquet at the expected `sports_reference` path. This was a `--dry-run`, so
   nothing was mutated. It is either a genuine large reference-data phantom incident or a stale/incomplete
   `candidate_parquet_paths` template. **A sports phantom run with `--apply` would flip ~721k reference rows to
   `attempted_failed` — so the count MUST be verified before anyone applies.**

## Current cockpit state (left intentionally as-is)

- `instruments-sports` card → `phantoms 721154` (amber), no reprobe line — legitimate reference audit output, kept.
- `market-data-sports` card → `reprobe 0 disagree`, no phantom line.
- cefi / prediction / tradfi cards → both lines (phantom + reprobe) on one card.
- defi → phantom line only; reprobe blocked separately by `read_manifest_index` single-shot `download_bytes` truncating
  on defi's large index (`ChunkedEncodingError`, 3/3 attempts) — a related but distinct read-path fragility worth its
  own fix.

## Decision

Operator decision 2026-07-14: **leave code as-is, document only.** No bucket-map change, no `--apply`, no market-data
sports phantom path added in this session. This doc tracks the inconsistency and the unverified count for a future
deliberate fix.
