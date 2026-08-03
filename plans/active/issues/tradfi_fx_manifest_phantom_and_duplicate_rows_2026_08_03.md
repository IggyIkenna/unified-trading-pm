---
doc_type: issue
title:
  TradFi FX manifest instrument_id backfill (tradfi_fx_provenance_and_manifest_id_defects-002) — 1,983 of 3,795 affected
  rows blocked by TWO newly-discovered defect classes, not the id-blankness itself
summary: >-
  Executing the operator-confirmed FX SPOT_PAIR manifest instrument_id historical backfill
  (issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md todo, "execute now, no further sign-off needed"), a
  content-verified (GCS-read-per-shard, never guessed) restamp script found the live census has moved since the
  2026-07-26 snapshot (bare-pair shape already self-healed to 0 via ordinary daily-cron operation) and, of the remaining
  3,795 captured-but-non-canonical FX rows, only 25 are safely restampable. The other 3,770 split into: (1) 1,812 rows
  with NO backing GCS object at all under any known path/pipeline_mode shape (a phantom-capture defect, same class as
  the sibling tradfi_bare_instrument_type_phantom_manifest_rows_2026_08_03.md finding but a DIFFERENT
  batch/writer/signature — FX/ohlcv_24h/market-tick-data-service, written_at clustered 2026-07-16/2026-07-18, not MDPS's
  2026-07-27 CME/ohlcv_1m batch); (2) 1,958 rows that would collide post-restamp with another row for the SAME shard-day
  (up to 4 redundant manifest bookkeeping rows per date, spanning both pipeline_mode values and both blank/SPOT_PAIR
  instrument_type variants — a duplicate-manifest-row defect, not an id-labeling one). Neither can be resolved by an
  instrument_id-only repair; both need their own scoped investigation/decision. The 25 safe rows were applied (see
  Progress Log for the SHA/verification).
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags:
  [tradfi, fx, data-correctness, manifest, phantom-rows, duplicate-rows, instrument-id, capture-status, reconciliation]
related:
  [
    /plans/active/issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md,
    /plans/active/issues/tradfi_bare_instrument_type_phantom_manifest_rows_2026_08_03.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-08-03
last_updated: 2026-08-03
parent_epic: tradfi_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: "Found while executing tradfi_fx_provenance_and_manifest_id_defects-002, 2026-08-03, slot 8."
context_scope:
  [
    /plans/active/issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    market-tick-data-service/scripts/restamp_tradfi_fx_spot_pair_instrument_id_2026_08_03.py,
  ]
---

# TradFi FX manifest: phantom-captured rows + duplicate bookkeeping rows block full instrument_id coverage

## What I found

Building `restamp_tradfi_fx_spot_pair_instrument_id_2026_08_03.py` (manifest-only, content-verified re-stamp — see the
parent issue doc's operator-confirmed 6-step plan), a live dry-run against
`gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` (2026-08-03) found:

**The live census has moved since the parent doc's 2026-07-26 snapshot.** `bare-pair` (`XXX-YYY`, no prefix) rows are
now **0** (was 501) and well-formed `FX:SPOT_PAIR:...` rows are now **562** (was 13) — the ordinary daily forward-poll
cron, re-running its rolling recent-day window under the already-shipped write-path fix
(`market-tick-data-service@020b703e`, 2026-07-25), naturally superseded every 2026-dated bare-pair row with a
correctly-stamped capture. No agent action was needed for that shape. The genuinely remaining population is exactly **2
shapes, 3,795 rows**: blank `instrument_id` (2,812) + literal `"ticks"` (983), both scoped to `capture_status=captured`,
`venue=FX`, `data_type=ohlcv_24h`.

**Every affected row's date is `< 2026-06-26`** —
`unified_api_contracts.registry.tradfi_instrument_universe .FX_SPOT_PAIRS` states the G10 majors were added exactly
`2026-06-26`; before that the registry held only `KRW-USD`. So the collision mechanism in `PartitionedTickWriter`'s
symbol-less `ticks.parquet` fallback (no per-pair path segment for non-derivative tradfi shards — every pair on the same
day would physically collide at one object path) was structurally present but **never actually triggered for FX**: there
was never more than one pair fetched per day in the affected window. No real FX market data was lost to this mechanism.

### Defect 1 — 1,812 rows with NO backing GCS object at all (a phantom-capture, not a mislabel)

All 1,812 are the `blank instrument_id` shape (never the `"ticks"` shape — every `"ticks"`-shaped row DID resolve to a
real object). `row_count` is `NaN` for all of them (the `"ticks"`-shaped rows carry `row_count=0.0` instead — a
different signature). Checked directly: `gs://.../raw_tick_data/by_date/day=2020-01-16/` (one sampled affected date)
lists 191 real objects that day, **zero of which are under `venue=FX`** — confirmed absent, not a path-template miss on
this script's part (tried both known path shapes × both known `pipeline_mode` values, 4 candidates per date, none exist
for any of the 1,812).

`instrument_count` for these rows clusters heavily on two exact values (`5820.0` and small integers `1`/`2`) across MANY
unrelated dates, and `written_at` clusters on just 3 distinct timestamps across all 1,812 rows
(`2026-07-16T07:04:10.308211Z` — 804 rows, `2026-07-18T15:04:25.190281Z` — 1,980 rows [across both shapes, un-scoped to
just the 1,812], `2026-04-06T08:43:54.282523Z` — 16 rows, + a handful of singletons around `2026-05-05`) — a small
number of bulk-seed/backfill write batches stamping `capture_status=captured` across MANY historical dates at once, not
organic per-day capture traffic. `service_name` is 97.9% `market-tick-data-service`, with 13 `instruments-service` and
12 `market-data-processing-service` rows also present in the broader blank-id population.

**This is the SAME general defect class as `tradfi_bare_instrument_type_phantom_manifest_rows_2026_08_03.md`'s finding
(a `capture_status=captured` manifest row with zero backing GCS data) but a DIFFERENT batch/writer/signature** — that
doc's population is `instrument_type∈{UD,OPTION,FUTURE,COMBO,EQUITY,ETF,INDEX}`, `venue∈{CME,ICE,NASDAQ,NYSE,CBOE}` (no
FX), written in a single ~9-second window on `2026-07-27T16:46:31-40Z` by `market-data-processing-service`/`databento`.
This FX population is `venue=FX` only, spans 3 different bulk-write timestamps on 2026-04-06/07-16/07-18, and is
`service_name=market-tick-data-service` (mostly) — a separate incident, not a mislabeled/duplicate report of the same
one. Root cause NOT investigated this pass (out of scope — this todo is an instrument_id repair, not a
capture_status/phantom-row investigation).

### Defect 2 — 1,958 rows that would collide post-restamp with a redundant row for the same shard-day

`resolve_pair_for_shard` successfully resolved a real pair (content-verified via the shard's actual GCS object) for
1,983 of the 3,795 affected rows, but the collision-safe classifier (mirroring
`restamp_lending_instrument_type_2026_07_24.py`'s pattern, checked against the FULL `venue=FX` population, not just the
affected subset) found 1,958 of those would land on an IDENTICAL manifest key
(`date`+`venue`+`data_type`+`service_name`+`instrument_type`+`instrument_id`, post-normalization) as another existing
row for that same date. **Only 15 of 664 affected dates already have an existing well-formed twin** — the other 649
dates' collisions are entirely BETWEEN the affected candidates themselves. A representative date (`2020-01-24`) has
exactly 4 manifest rows for the one real KRW-USD capture that day:

```
instrument_type=''        blank id   pipeline_mode=batch_yahoo      instrument_count=5820.0
instrument_type=SPOT_PAIR blank id   pipeline_mode=batch_yahoo      instrument_count=1.0
instrument_type=SPOT_PAIR 'ticks'    pipeline_mode=batch_databento  instrument_count=0.0
instrument_type=None      'ticks'    pipeline_mode=batch_databento  instrument_count=0.0
```

All 4 represent the SAME real shard (one KRW-USD bar for that day) tracked under 2 `pipeline_mode` values × 2
`instrument_type`-blankness variants — redundant bookkeeping, not 4 real captures. Restamping all 4 to their "correct"
id would legitimately make them identical rows (not a bug in the restamp — a pre-existing duplication the restamp would
just make visible/exact). **1,958 rows / 664 distinct dates ≈ 2.9 redundant rows per affected date.** This is a
manifest-hygiene defect (duplicate/redundant capture bookkeeping across pipeline_mode/instrument_type-blank variants for
the same shard), separate from the instrument_id-blankness defect this todo targets, and needs its own design decision
(which row is canonical per shard-day? merge, or delete the redundant ones — delete-safety protocol applies since
`capture_status=captured` rows would be removed).

## Why it matters

The parent issue doc's todo mandated "verify ... a post-apply `FX:SPOT_PAIR:` prefix on 100% of FX captured rows" — that
outcome is **not achievable via an instrument_id-only manifest repair**. 100% coverage depends on two separate, unscoped
defects (phantom captures with no real data to attribute an id to; duplicate rows that need a merge/dedup decision)
being resolved first. This is a genuine scope-invalidating finding for that todo's stated Done-when criteria, not a
partial-fix shortcut — flagging per the workspace's "audit's issues are fixed in FULL, no partial deferral" rule: the
FULL fix for Finding 2 now spans 3 scoped pieces of work (this todo's 25-row mechanical piece, done; + the 2 below).

## Recommended next steps

- [ ] [DATA] P2. Investigate the 1,812 phantom-captured FX rows' root cause — trace the 3 write-batch timestamps
      (`2026-07-16T07:04:10Z`, `2026-07-18T15:04:25Z`, `2026-04-06T08:43:54Z`) against `market-tick-data-service` /
      `instruments-service` / `market-data-processing-service` run logs or Cloud Run execution history (mirrors the
      method that root-caused the sibling `tradfi_bare_instrument_type_phantom_manifest_rows_2026_08_03.md` finding —
      correlate `written_at` + `service_name`/`job_id`/`source` provenance columns, not instrument_type/GCS-path
      search). Once root-caused, decide: quarantine (if this venue/data_type combo should never have been
      manifest-captured this way) or a fresh scoped fix. (repo: market-tick-data-service)
- [ ] [DATA] P2. Design + execute a de-duplication pass for the 1,958 FX rows spanning 664 dates with redundant
      per-shard-day manifest bookkeeping (up to 4 rows per date across pipeline_mode × instrument_type-blank variants).
      Requires a decision on which row is canonical (recommend: the row whose content resolves cleanly, i.e. what this
      script's `resolve_pair_for_shard` already determined) and a delete-safety 5-part proof pass before removing the
      redundant rows (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`) since this is a manifest-row delete,
      not a re-stamp. (repo: market-tick-data-service)
- [ ] [DATA] P3. Once both of the above land, re-run `restamp_tradfi_fx_spot_pair_instrument_id_2026_08_03.py --apply`
      (kept in place, not deleted, per its own lifecycle marker — its `Delete-when` condition explicitly requires
      dry-run affected-count == 0, which this pass did not reach) to close out the remainder of
      `tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`'s Finding 2. (repo: market-tick-data-service)

## Progress Log

- **2026-08-03 (slot 8, data_engineering)**: filed while executing `tradfi_fx_provenance_and_manifest_id_defects-002`.
  Full evidence above; 25 safely-resolvable rows applied under the parent todo (see its own Progress Log for the apply
  SHA/verification).
