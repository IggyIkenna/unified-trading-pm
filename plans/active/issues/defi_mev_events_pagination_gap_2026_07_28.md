---
doc_type: issue
title: "collect-mev-events pagination gap — mev_events_handler.py hard-exits after the first Flashbots relay page, under-covering any day with >100 MEV-Boost relay payloads"
summary: >-
  `_fetch_mev_events()` in `market-tick-data-service/market_tick_data_service/cli/handlers/mev_events_handler.py` pages
  the Flashbots relay `proposer_payload_delivered` endpoint at 100 rows/request but the pagination loop hard-exits after
  the FIRST successful page regardless of how many payloads remain for the day (`cursor = from_slot` on the "keep
  going" branch, which is the same sentinel the loop's own `while cursor > from_slot` condition uses to terminate —
  line 235). Any day with more than ~100 MEV-Boost relay payloads across the requested slot range therefore only
  captures its newest ~100 rows; the rest are silently never fetched (no error, no `attempted_failed` row — the
  handler returns a truncated-but-successful row count and `record_captured` stamps it as complete). Already fully
  root-caused (not re-investigated here) in
  `plans/archive/issues/defi_five_never_captured_venues_fix_2026_07_22.md` § "FLASHBOTS (mev_events) -- NEVER
  SCHEDULED", deferred-work row "File the mev_events >100-payload/day pagination gap".
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [defi, mev_events, flashbots, pagination, honest-absence, data-completeness]
related:
  [
    plans/archive/issues/defi_five_never_captured_venues_fix_2026_07_22.md,
    plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-28
parent_epic: defi_master
source: [data_engineering slot-11, 2026-07-28, dispatched via defi_satellite_ao_dispatch_batch1-015]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.16
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-28
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

## What I found

`mev_events_handler.py`'s `_fetch_mev_events()` (`market-tick-data-service/market_tick_data_service/cli/handlers/mev_events_handler.py:181-240`)
fetches the Flashbots relay `proposer_payload_delivered` feed for a target day by walking a slot-cursor backwards from
`to_slot` (the end of the day) toward `from_slot` (the start of the day), 100 rows per request
(`market_tick_data_service/cli/handlers/mev_events_handler.py:199-208`):

```python
# Fetch in pages (100 per request)
cursor = to_slot
while cursor > from_slot:
    batch_limit = min(100, cursor - from_slot)
    ...
    if len(data) < batch_limit:
        break
    cursor = from_slot  # exit after first batch (avoid excessive API calls)   # <-- mev_events_handler.py:235
```

Line 235 is reached whenever the first page comes back FULL (`len(data) >= batch_limit`, i.e. there IS more data to
page through) — and it sets `cursor = from_slot`, which is exactly the loop's own termination value for
`while cursor > from_slot`. So the very next loop check exits, even though the correct pagination step would be
`cursor -= batch_limit` (or the oldest slot number seen in the current page) to keep walking backward toward
`from_slot`. The comment ("avoid excessive API calls") documents this as a deliberate cap, not a bug in intent — but
the effect is a silent, uncapped-severity data gap: any day whose relay volume across the ~7200-slot (~24h) window
produces more than one page (>100 rows) only ever captures its NEWEST ~100 rows; the remainder of the day's MEV-Boost
relay payloads are never fetched.

This is NOT surfaced as a failure anywhere in the pipeline: `_fetch_write_record()` (mev_events_handler.py:119-178)
treats any non-empty `rows` list as a full success — `write_defi_rows()` writes the (truncated) rows,
`recorder.record_captured(...)` stamps `capture_status=captured` with the truncated `row_count`
(mev_events_handler.py:151-159). There is no partial/truncated state in the 4-state `capture_status` model this
writer emits into — a day with 100 MEV-Boost relay payloads and a day with 5,000 both read identically as "captured"
in the availability manifest, differing only in `row_count`, which nothing currently gates on.

## Why it matters

- **Silent under-coverage, not an outage** — the handler never errors, never records `attempted_failed`, and never
  triggers a retry/backfill signal. The only way to notice the gap today is to compare `row_count` against an
  out-of-band expectation (e.g. cross-checking against a public MEV-Boost relay dashboard), which nothing in this
  pipeline currently does.
- **Severity scales with relay activity, not with the bug** — Flashbots alone regularly delivers well over 100
  proposer-payload records per day on mainnet (roughly one per 12s slot when Flashbots wins the auction), so this is
  very likely tripping on most or all production days, not an edge case.
- **Downstream consumers get a biased sample** — any `mev_events` consumer (MEV-Boost relay-share analytics,
  builder/relay concentration metrics, DeFi execution-cost features) is silently working off "newest ~100 payloads of
  the day" rather than "the day's payloads," which skews time-of-day distribution (relay activity is not uniform
  across a day) without any indication in the data that it's a partial sample.

## Recommended decision

Fix the pagination step so the loop actually walks the full requested slot range instead of hard-exiting after page 1:
replace `cursor = from_slot` (mev_events_handler.py:235) with a real cursor decrement — e.g.
`cursor = min(_to_int(block.get("slot"), cursor) for block in data) - 1` (oldest slot seen in the current page, minus
one) or simply `cursor -= batch_limit` if the API's `cursor` param is a plain slot-count offset rather than an
absolute slot number (needs a one-off API-contract check against the Flashbots relay docs/response shape before
picking between the two — both are simple, mechanical fixes once confirmed). No schema/contract change needed; this is
contained entirely inside `_fetch_mev_events()`.

- [ ] [BACKEND] P2. Fix the `_fetch_mev_events()` pagination cursor step in
      `market-tick-data-service/market_tick_data_service/cli/handlers/mev_events_handler.py:235` so the loop pages
      through the FULL target-day slot range (`from_slot`..`to_slot`) instead of hard-exiting after the first
      100-row page — confirm whether the Flashbots relay `cursor` query param is an absolute slot number or a
      page-offset before choosing the exact decrement, add a unit test with a mocked >100-row multi-page response
      asserting all pages are fetched and merged, and re-run a live sample-day backfill to confirm `row_count` now
      exceeds 100 on a day with known relay volume >100 payloads. Repo: market-tick-data-service. Source: this doc.
