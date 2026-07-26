---
doc_type: issue
title:
  30/200 sampled canonical sports MDT (market-tick-data) odds objects carry duplicate rows on the poll key (event,
  market, outcome, bm_time, price, fetch_utc) — independent of the OR-5b legacy→canonical cutover
summary: >-
  During the OR-5b legacy→canonical MDT investigation, a 200-object sample of canonical
  `market-data-tick-sports-prd-central-element-323112` odds objects found 30/200 (15%) already carry duplicate rows on
  the poll key `(event, market, outcome, bm_time, price, fetch_utc)`. This is a pre-existing data-quality defect in
  canonical's own captured population, unrelated to the legacy-bucket recovery the investigation was scoped around — the
  32-day legacy→canonical recovery that would have de-duplicated ON WRITE for its own merged rows (step 2 of that
  procedure) has since been ABANDONED (operator ruling 2026-07-25, source legacy bucket deleted 2026-07-17 before
  recovery ran — see `mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md`), so no mechanism currently plans to
  touch the 30/200 sampled duplicates or the wider canonical population they were sampled from. This doc exists purely
  to track the standalone finding + the still-open remediation now that the only planned dedup path is gone.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [mdt, sports, odds, duplicate-rows, poll-key, data-correctness, canonical]
related:
  [
    /plans/active/issues/mdt_legacy_canonical_row_gap_2026_07_16.md,
    /plans/archive/issues/mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
priority: P3
parent_epic: sports_master
source:
  "Loose-end #5 of the OR-5b legacy→canonical MDT investigation (mdt_legacy_canonical_row_gap_2026_07_16.md, 2026-07-16
  read-only pass), documented per that doc's own triage as requiring a standalone issue doc; filed as
  sports_satellite_ao_dispatch_batch2-013 (2026-07-25, slot 9)."
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# Canonical sports MDT odds objects — 30/200 sampled carry duplicate rows on the poll key

## What I found

While investigating the OR-5b legacy→canonical MDT row gap (see `issues/mdt_legacy_canonical_row_gap_2026_07_16.md`), a
200-object sample of **canonical** (`market-data-tick-sports-prd-central-element-323112`) odds objects found **30/200
(15%) already carry duplicate rows** on the poll key `(event, market, outcome, bm_time, price, fetch_utc)` — i.e. more
than one row sharing the same event/market/outcome/bookmaker-timestamp/price/fetch-timestamp tuple within the same
object.

This is **independent of the legacy→canonical cutover** the parent investigation was scoped around: the duplicates are
already present in canonical's own captured population, not something the (now-abandoned) 32-day recovery merge would
have introduced. The parent doc's step 2 spec ("de-dup on write on the poll key `(event,market,outcome,bm_time,price)`")
would only have de-duplicated the _newly merged_ rows for that specific 32-day recovery — it never covered the
already-existing duplicates in the wider canonical population this 200-object sample was drawn from.

**The only planned remediation path for this finding is now gone.** The 32-day legacy→canonical recovery has been
**ABANDONED** (operator ruling 2026-07-25 — the source legacy bucket was deleted 2026-07-17T17:05:17Z before STEP 1 ever
ran; see `issues/mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md`). That recovery's step 2 was the only concrete
dedup-on-write mechanism named anywhere in the investigation, and it will never execute.

## Why it matters

- Duplicate rows on the poll key double-count identical price observations in any per-book/per-market aggregate
  (dispersion, spread, book-depth-adjacent stats) that reads these objects without its own dedup step — a data-quality
  defect for downstream consumers, not just a storage inefficiency.
- 15% of a 200-object sample is not a rounding artifact; it implies a real fraction of the canonical odds corpus is
  affected, though the true population-wide rate and root cause (writer-side retry double-write? multiple capture passes
  merged without a dedup step? a genuine re-poll landing on an identical price?) were never diagnosed — the parent
  investigation was scoped to the legacy/canonical row-count gap, not to root-causing this defect.
- Without a fix, any future writer/merge into this population risks perpetuating or compounding the duplication (the
  same failure mode the abandoned recovery's step 2 was meant to guard against for its own writes).

## Recommended decision

1. **Root-cause the duplication mechanism** on a fresh sample (the original 30/200 sample was not preserved as a
   reproducible artifact) — determine whether it's a writer-side retry/multi-write defect (in which case the writer
   needs a dedup-on-write guard, mirroring the `player_stats` writer-side de-dup fix shipped in
   `instruments-service@210d4567` for a structurally similar defect) or a merge-time artifact from an unrelated prior
   campaign.
2. **Measure the population-wide rate** via the availability manifest (single-walk discipline — do not re-walk the
   corpus ad hoc) to size the actual scope before committing to a full backfill-style de-dup rewrite.
3. **If population-wide de-dup is warranted**, it is a scoped rewrite job analogous to the `player_stats` de-dup rewrite
   (`instruments-service@210d4567`, `scripts/dedup_canonical_player_stats_2026_07_25.py`) — read affected objects,
   de-dup on the poll key, re-write, verify by content (0 duplicates remain).
4. This is a genuinely separate, currently-unowned piece of work now that the recovery plan it was folded into is
   abandoned — recommend a new `[DATA]` fix todo be picked up against this doc rather than assuming it is covered
   elsewhere.

- [x] ✅ [DATA] P3. **DONE 2026-07-26 (slot-8, `data_engineering`) — measured rate is 10-50x LOWER than the original
      30/200 sample, and the mechanism is NOT a writer-side retry.** Built + live-tested (2 independent random samples,
      seeds 42 and 777, n=300 each, against real prod objects — no fresh corpus walk, single bounded
      `read_availability_index` read) `scripts/measure_odds_api_poll_key_duplicates_2026_07_26.py`. **Rate: 1/300 (0.3%)
      and 3/300 (1.0%)** affected objects across the two independent samples — 4 total affected objects out of 600
      sampled (~0.67%), NOT the originally-reported 15%. The real column names are `event_id`/`market_key`/
      `outcome_name` (the doc's `event`/`market`/`outcome` was shorthand); GCS path is
      `raw_tick_data/by_date/day={D}/pipeline_mode=batch_odds_api/asset_group=sports/venue={V}/league_id={L}/     instrument_type={ODDS|odds}/data_type={TRADES|trades}/ticks.parquet`
      (empirically verified via `gcloud storage     ls`, no existing SSOT path builder for this domain — unlike
      `sports_reference/`'s `candidate_parquet_paths`). **Root cause (all 4 affected objects, not just one spot-check):
      NOT a writer-side retry/multi-write — every duplicate-key group (0/11 fully byte-identical across ALL columns)
      differs specifically in `instrument_id`.** Direct inspection of the first affected object
      (`2022-09-04/BETONLINEAG/K_LEAGUE_1`) shows the SAME real price observation (`event_id`, `market_key`,
      `outcome_name`, `bm_time`, `price`, `fetch_utc` all identical) recorded under TWO different `instrument_id`
      strings — `FOOTBALL:BETONLINEAG:MATCH_ODDS:K_LEAGUE_1:2022-23:SEONGNAM-ULSAN_HYUNDAI_FC::{sel}` vs.
      `FOOTBALL:BETONLINEAG:MATCH_ODDS:K_LEAGUE_1:2022-23:SEONGNAM_FC-ULSAN_HYUNDAI_FC::{sel}` — a team-name resolution
      split ("SEONGNAM" vs "SEONGNAM_FC" for the same real team), not a poll-key collision from a genuine re-fetch.
      UAC's `build_instrument_id` (`unified_api_contracts/canonical/domain/sports/canonical_ids.py:214`) takes
      `home_team_id`/`away_team_id` as caller-supplied inputs — it's the UPSTREAM team-name→team_id resolution (in
      `market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py` or whatever calls this builder)
      that's producing two different id strings for one real team across different polls; not traced to the exact
      resolution line this pass (flagging with the confirmed evidence rather than guessing further). **This changes the
      Step-2 remediation**: a blind `drop_duplicates(subset=poll_key, keep="first")` (the player_stats precedent's
      pattern) would be WRONG here — it would arbitrarily keep whichever spelling happens to sort/appear first, silently
      discarding rows under the OTHER (possibly-canonical) `instrument_id` without ever checking which spelling is
      actually correct. Re-scoped the fix todo below accordingly.
- [ ] [DATA] P3. **Fix the team-name resolution split causing duplicate `instrument_id`s (repo:
      market-tick-data-service)** — NOT a blind poll-key de-dup (see the finding above for why that would be wrong
      here). Step (a): trace the exact home/away team-name→team_id resolution feeding `build_instrument_id`'s calls in
      the odds-api sports write path and confirm why the SAME real team resolves to two different id fragments (e.g.
      "SEONGNAM" vs "SEONGNAM_FC") on different polls — likely a missing/incomplete team-name alias table entry,
      mirroring `unified_api_contracts/external/api_football/team_mappings.py`'s pattern but for whatever odds-api's own
      team-name source is. Step (b): once the CURRENT canonical spelling is confirmed, re-run this doc's measurement
      script (`measure_odds_api_poll_key_duplicates_2026_07_26.py`) against the FULL population (not a sample) to get
      the exact affected-object count, then write a scoped rewrite that keeps the rows under the confirmed-canonical
      `instrument_id` and drops the stale-spelling rows (not a bare `keep="first"`). **Done when**: the team-name
      resolution root cause is confirmed with the exact code location, the full-population affected-object count is
      measured, and a re-run over the affected population confirms 0 poll-key duplicates remain under the canonical
      spelling.

## Progress Log

**2026-07-25 (slot 9)** — Filed per `sports_satellite_ao_dispatch_batch2-013` (this todo is documentation-only; the fix
todos above are new, standalone work, not yet dispatched or claimed by any other plan).

**2026-07-26 (slot-8, `data_engineering`)** — closed the root-cause + measure todo. Real population-wide rate (0.3%-1.0%
across 2 independent 300-object samples) is materially lower than the original 30/200 (15%) figure, and the mechanism is
a team-name/`instrument_id` resolution split, not a writer-side retry. Re-scoped the remediation todo away from the
player_stats-style blind poll-key de-dup (which would have been actively wrong here — it would silently pick an
arbitrary spelling rather than the canonical one). Did not attempt the team-name-resolution fix itself this pass (needs
its own trace + a canonical-spelling decision).
