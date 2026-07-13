---
doc_type: issue
title:
  OnchainPerpBatchHandler deliberately writes ZERO manifest rows for "live-only" data types — structurally incompatible
  with Layer-1's "every EXPECTED tuple needs >=1 row" completeness requirement
summary:
  'Found 2026-07-12 while investigating the mvp_backfill_cefi_tick_v10 G4 Layer-1 gate — specifically the 4 remaining
  book_snapshot_5-only tuples (ASTER, EXTENDED-STARKNET, LIGHTER-ZKSYNC, PACIFICA-SOLANA) plus LIGHTER-ZKSYNC/trades and
  ASTER/liquidations. Root cause (confirmed via code read,
  market_tick_data_service/cli/handlers/onchain_perp_batch_handler.py:180-239, `_LIVE_ONLY_DATA_TYPES` +
  `_batch_data_types_for_venue`): these (venue, data_type) pairs are deliberately excluded from the batch/historical
  capture universe because their REST endpoints only expose CURRENT state (no historical range param — e.g. Extended
  `/info/markets/{symbol}/orderbook`), so a live WebSocket connector is meant to capture them going forward instead. The
  exclusion path explicitly does NOT write an empty_confirmed row ("never an empty_confirmed cell (the honest model is
  live-only, not impossible)" per the code comment) — it writes NOTHING to the manifest for that shard-day. This is a
  genuine architecture contradiction, not a bug I can safely patch solo: Layer-1s completeness check
  (check_enumeration_completeness.py) requires every EXPECTED (venue, instrument_type, data_type) tuple to have AT LEAST
  ONE manifest row of ANY capture_status to count as "present" — a tuple this handler NEVER writes ANY row for can never
  satisfy Layer-1, meaning cefi Layer-1 100%/denominator_complete=True is UNREACHABLE as currently coded, for as long as
  these tuples remain in the UAC EXPECTED denominator.'
status: open
nature: notes
asset_group: [cefi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags:
  [
    honest-coverage,
    denominator-audit,
    layer-1,
    data-correctness,
    architecture-contradiction,
    cefi,
    live-only,
    onchain-perp,
    mvp-backfill-v10,
  ]
related:
  [
    mvp_backfill_cefi_tick_v10_2026_06_27.md,
    cefi_layer1_denominator_gaps_2026_07_03.md,
    cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md,
    ../../../codex/02-data/honest-coverage-model.md,
    ../../../codex/02-data/availability-manifest-and-data-status.md,
    ../../../codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-12
parent_epic: cefi_master
priority: P1
source: mvp_backfill_cefi_tick_v10_2026_06_27.md G4 re-verification, 2026-07-12 session (via sub-agent code trace)
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
assigned_role: data_engineering
model_tier: sonnet-doable
thinking_tier: high
drift_direction: advance-code
depends_on: []
---

## What I found

`market_tick_data_service/cli/handlers/onchain_perp_batch_handler.py:196-201` declares:

```python
_LIVE_ONLY_DATA_TYPES: dict[str, frozenset[str]] = {
    "ASTER": frozenset({"book_snapshot_5", "liquidations"}),
    "PACIFICA-SOLANA": frozenset({"book_snapshot_5"}),
    "EXTENDED-STARKNET": frozenset({"book_snapshot_5"}),
    "LIGHTER-ZKSYNC": frozenset({"trades", "book_snapshot_5"}),
}
```

`_batch_data_types_for_venue()` (lines 234-239) filters these OUT of the batch capture universe before the per-shard
loop runs, logging `"OnchainPerpBatch: excluding %s/%s from batch universe (live-only) — not attempted"` and **writing
zero manifest rows** — confirmed via `run.log` for `cefi-extended-starknet-2024-20260712-055837`: every single day in
the shard range logs this exclusion for `book_snapshot_5`, with `0 rows` reported for that data_type, and no
`attempted_failed`/`empty_confirmed` row appears anywhere in the manifest for it (cross-checked against the Layer-1
missing-tuples list — `(EXTENDED-STARKNET, perpetual, book_snapshot_5)` is a hard MISSING, not present-as-empty).

**This is a deliberate design choice**, not an oversight — the code comment explicitly rejects writing
`empty_confirmed`: "never an empty_confirmed cell (the honest model is 'live-only', not 'impossible')". The stated plan
is for a live WebSocket connector to capture these feeds going forward, with no attempt to backfill history
(structurally impossible — the REST endpoints only expose current state).

## Why it matters (the contradiction)

Two design principles in this codebase are now in direct conflict for these specific (venue, data_type) pairs:

1. **Layer-1 completeness** (`check_enumeration_completeness.py::_build_enumerated_tuples`, docstring: "across all 4
   capture_status states") requires every UAC EXPECTED tuple to have >=1 manifest row of ANY status
   (`captured`/`attempted_failed`/`empty_confirmed`/`expected_unattempted`) to count as "present" in the ENUMERATED
   matrix. The `mvp_backfill_cefi_tick_v10` plan's G4 gate requires `denominator_complete == True` (zero missing
   tuples).
2. **OnchainPerpBatchHandler's live-only exclusion** deliberately writes NOTHING for these tuples — not even a typed
   `empty_confirmed[EXPECTED_...]` row, unlike every other honest-absence case in this codebase (e.g. DERIBIT-COMBO's
   documented target state, HL/ASTER's other documented deferred-no-source carve-outs which DO write typed-empty rows
   per `codex/02-data/honest-absence-downstream-handling.md`).

**Result**: as currently coded, principle (2) makes principle (1) permanently unsatisfiable for 6 tuples (ASTER
book_snapshot_5, ASTER liquidations [already excluded from Layer-1 scope per data_type sparsity], PACIFICA-SOLANA
book_snapshot_5, EXTENDED-STARKNET book_snapshot_5, LIGHTER-ZKSYNC trades, LIGHTER-ZKSYNC book_snapshot_5) — no backfill
VM, no relaunch, no retry will EVER close these Layer-1 tuples while both pieces of code stay as they are. This is
exactly the kind of "SSOT contradiction" this workspace's findings-triage rules flag for operator notification rather
than a unilateral fix, because there are two structurally different resolutions with different tradeoffs (see below) and
I don't have the authority/context to pick one.

**Note on LIGHTER-ZKSYNC/trades**: this tuple does NOT currently appear in the Layer-1 missing-tuples list (it resolved
after today's venue-allowlist fix, `market-tick-data-service@57493789` etc.) — worth double-checking whether that's
because (a) a genuinely different Tardis-based code path (documented elsewhere as "Post-2026-04-17: Tardis carries
trades + book_snapshot_5 + derivative_ticker" for lighter) now captures it for recent dates, bypassing this handler's
`_LIVE_ONLY_DATA_TYPES` exclusion entirely for post-04-17 dates, in which case the SAME Tardis post-04-17 path might
also be able to serve `book_snapshot_5` for LIGHTER-ZKSYNC (a genuine backfill fix, not a denominator/contradiction
issue) — NOT verified this session (time-boxed; flagging as a concrete next check).

**UPDATE 2026-07-12T09:20Z — a 7th tuple in the same class found: `(COINBASE-CDE, future, trades)`.** Confirmed via
code: `market_tick_data_service/live/connectors/coinbase_cde_ws.py` is the ONLY capture path for this venue — a LIVE
WebSocket connector, no batch/historical adapter exists at all. UAC's own comment
(`venue_constants.py`/`market_data_categories.py` `VENUE_DATA_TYPE_CAPABILITIES["COINBASE-CDE"]`) explicitly says
"Live-only for now: Tardis has ZERO coverage of this venue under any name... only the re-keyed coinbase_cde_ws.py live
connector... captures real data." Start date is honestly floored to `2026-07-10` (venue registration date, no fabricated
pre-registration history) — same "no backfill possible, live-only" shape as the 6 DEX-venue tuples above, just a CEX
case this time. Not yet verified whether the live connector is actually deployed/running (if it's simply not deployed
yet, that's a separate, unrelated deployment gap, not this architecture contradiction) — but if it IS running, this
tuple faces the exact same mathematical-unreachability problem and should be covered by whichever resolution (a) or (b)
below gets picked, generalized to "live-only across ALL asset classes", not just the onchain-perp handler specifically.

## Recommended decision (operator/architecture call — NOT mine to make unilaterally)

Two structurally different resolutions, each with real tradeoffs:

- **(a) Correct the UAC denominator**: drop these 6 tuples from `INSTRUMENT_TYPES_BY_VENUE` /
  `VENUE_DATA_TYPE_CAPABILITIES` (mirrors the BITFINEX-FUTURES precedent shipped today,
  `unified-api-contracts@5b57c2b2`) — treats "live-only, no historical backfill possible" as equivalent to "this venue
  doesn't offer this data_type for batch capture", which is arguably true. **Tradeoff**: silently narrows the MVP's
  stated data scope for these DEX venues without an explicit operator sign-off that book_snapshot_5/trades depth for
  these 4 venues is acceptably out of scope forever.
- **(b) Make OnchainPerpBatchHandler write a typed `empty_confirmed[EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE]`-shaped
  row instead of nothing** for live-only exclusions (mirrors the DERIBIT-COMBO/HL/ASTER honest-absence pattern already
  used elsewhere in this exact codebase) — keeps the tuples in the denominator (documenting the real, if permanent, gap)
  while making Layer-1 mathematically satisfiable. **Tradeoff**: this is templated code (per-shard-day writes across
  potentially years of date range × symbols), non-trivial to retrofit cleanly, and changes the manifest's historical
  semantics for these cells going forward (existing runs already skipped these days with zero rows — would need either a
  one-time backfill-the-typed-empty-rows script, similar in shape to
  `relabel_deribit_combo_historical_to_empty_2026_06_27.py`, or acceptance that only NEW runs get the typed row while
  historical days stay silently absent).

My recommendation, if asked: **(b)**, because it's consistent with every other honest-absence precedent in this codebase
and because (a) requires an explicit "we're giving up on this data forever" scope decision that should be an operator
call, not something inferred from a code-reading session. But I am NOT implementing either without operator sign-off —
this affects the MVP data scope, which per CLAUDE.md's "Findings triage" HARD RULE is a big finding (data-correctness /
SSOT contradiction) requiring NOTIFY OPERATOR.

## Todos

- [x] ✅ [DESIGN] P1. Operator decision: resolution (a) denominator-correction vs (b) typed-empty-row retrofit for the 6
      live-only tuples (ASTER/book_snapshot_5, ASTER/liquidations, PACIFICA-SOLANA/EXTENDED-STARKNET/LIGHTER-ZKSYNC
      book_snapshot_5, LIGHTER-ZKSYNC/trades). (repo: unified-trading-pm, for the decision; implementation repo depends
      on the choice) — **✅ DECIDED + IMPLEMENTED 2026-07-13 (slot-2)**: operator ruled option **(b)** via `/blocked` —
      "write a typed empty_confirmed[EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE] row instead of dropping the 6 tuples from
      the UAC denominator. Matches the existing DERIBIT-COMBO/HL/ASTER honest-absence precedent and CLAUDE.md's 'never
      silent placeholders' rule." Implemented in `OnchainPerpBatchHandler`: added `_record_live_only_empty_rows`, called
      right after `_batch_data_types_for_venue` filters live-only data_types out of the batch universe — writes one
      typed row per (data_type, symbol) excluded for that reason, for ALL 6 tuples (not 5 — the exclusion logic was
      already scoped correctly, my earlier own summary undercounted this in one place, corrected here). DROPPED
      data_types (no feed on ANY transport, e.g. HL liquidations) are unaffected — "never attempted" stays correct for
      them, per the operator's own framing (only LIVE-ONLY tuples were in scope for (a)/(b)). Split the exclusion logic
      (dicts + filter + new recorder) into a new `_onchain_perp_batch_live_only.py` stage module to stay under the
      900-line codex ratchet (pure code motion for the pre-existing pieces, mirrors the existing
      `_onchain_perp_batch_lighter.py`/`_umi.py` splits). 4 tests updated (ASTER/PACIFICA/EXTENDED book_snapshot_5 now
      assert `record_empty` IS called with the typed reason, was `assert_not_called()`) + 1 new test (LIGHTER-ZKSYNC
      trades+book_snapshot_5). Full `quality-gates.sh` green (fresh run, not sentinel-cached). Shipped
      `market-tick-data-service@3dd28d5e`. **Live-verified the code path** (not just unit tests): a dry-run CLI
      invocation
      (`--operation collect-onchain-perp-batch --venues ASTER --onchain-perp-data-types     book_snapshot_5 --dry-run`)
      showed the exclusion log line immediately followed by "ManifestWriter: DRY RUN — would have written 1 rows" (0
      rows would have been logged pre-fix); a REAL (non-dry-run) invocation reached the identical point and repeatedly
      attempted the real GCS write, hitting ONLY the pre-existing, unrelated `ManifestWriter` generation-CAS retry loop
      (heavy concurrent-slot contention on the shared cefi manifest this session — 13 consecutive retries, all clean
      backoff-and-retry, zero errors, killed by my own CLI timeout before attempt 15/15 exhausted, not a bug) — never a
      code exception, never wrong data. **This is a going-forward fix only**: existing historical shard-days that
      already silently skipped stay silently absent unless separately backfilled (not attempted this session — a
      distinct, lower-priority follow-up, similar in shape to `relabel_deribit_combo_historical_to_empty_2026_06_27.py`,
      left for whoever picks up P3 below).
- [x] [SCRIPT] P2. Check whether LIGHTER-ZKSYNC's post-2026-04-17 Tardis-routed capture path (the one that resolved
      `trades` today) can also serve `book_snapshot_5` — if so this ONE tuple may be a genuine backfill fix independent
      of the (a)/(b) decision above, narrowing the live-only set to 5 tuples. (repo: market-tick-data-service) **DONE
      2026-07-12 (slot-10) — answer is NO, does not narrow the set.** Confirmed via 3 independent sources, all
      consistent: (1) `_onchain_perp_batch_lighter.py`'s module docstring, explicit and unambiguous — "LIGHTER-ZKSYNC's
      own REST (`/recentTrades`, `/orderBookOrders`) is snapshot-only... so `trades`/`book_snapshot_5` are excluded from
      the batch universe entirely... `derivative_ticker` (funding) has NO native-REST source at all — its only batch
      source is Tardis" — i.e. Tardis's coverage for this venue is `derivative_ticker` ONLY, never
      `trades`/`book_snapshot_5`. (2) The commit that actually wired Tardis for this venue
      (`market-tick-data-service@57493789`, "wire LIGHTER-ZKSYNC derivative_ticker into OnchainPerpBatchHandler via
      Tardis") says so explicitly in its own message: "trades/book_snapshot_5 stay excluded (live-WS-only, no historical
      REST source)" — it only ever touched `derivative_ticker`. (3) Direct manifest read
      (`market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`): **zero rows of any
      capture_status** for LIGHTER-ZKSYNC × `{trades, book_snapshot_5}` — both are equally, symmetrically absent, no
      partial/historical coverage for either. So `book_snapshot_5` stays in the live-only set; the live-only tuple count
      is still 6, not narrowed to 5. **Separately, could NOT resolve the `trades`-dropped-off-the-missing-list puzzle
      the issue doc flagged** (its own framing already correctly hedged this as unverified) — `57493789` never touches
      `trades` at all per its diff/message, and `instruments-service/scripts/check_enumeration_completeness.py` has no
      LIGHTER-ZKSYNC-specific carve-out either, so whatever changed `trades`'s Layer-1 missing-status is neither of the
      2 places I checked. Since `trades` has zero manifest rows (same as `book_snapshot_5`, confirmed above), it's NOT
      because of new captured data — likely a denominator-side change from a different, not-yet-identified commit
      ("etc." in the original finding). Leaving this genuinely unresolved rather than guessing; does not affect the P1
      operator decision (both `trades` and `book_snapshot_5` for LIGHTER-ZKSYNC are still in the 6-tuple live-only set
      either way, since this todo's actual question — can Tardis serve `book_snapshot_5` — is answered). No code change
      — investigation only; issue doc ships via the PM `docs(plans):` carve-out.
- [x] ✅ [SCRIPT] P3. Once (a) or (b) is decided and implemented, re-run `measure_honest_coverage.py --asset-group cefi`
      to confirm Layer-1 tuple count drops accordingly. (repo: instruments-service) — **DONE 2026-07-13 (slot-6)**: ran
      a real
      `collect-onchain-perp-batch --venues ASTER PACIFICA-SOLANA EXTENDED-STARKNET LIGHTER-ZKSYNC --start-date     2026-07-11 --end-date 2026-07-11 --onchain-perp-symbols BTC`
      (scoped to 1 symbol to bound the shared-manifest contention this session hit repeatedly). All 6 live-only
      exclusion log lines fired + all 6 typed `empty_confirmed` rows landed in the manifest (verified by direct query,
      not just the log). Re-ran `measure_honest_coverage.py --asset-group cefi`: Layer-1 missing-tuple count dropped and
      Layer-1 completeness rose from 90.4% → 93.2% (73 EXPECTED, missing 7→5). **Confirmed via full missing-tuple list
      (not just the logged first-5)**: none of the 6 original live-only tuples (ASTER book_snapshot_5/liquidations,
      PACIFICA-SOLANA book_snapshot_5, EXTENDED-STARKNET book_snapshot_5, LIGHTER-ZKSYNC trades/book_snapshot_5) remain
      missing — the 5 tuples still missing are all pre-existing, unrelated gaps (BITGET-FUTURES x3, COINBASE-CDE/trades,
      DERIBIT-COMBO/trades). **Sub-finding**: the first pass showed 2 of the 6 rows (EXTENDED-STARKNET/book_snapshot_5,
      LIGHTER-ZKSYNC/book_snapshot_5) logged as successfully written but verifiably ABSENT on direct manifest query —
      root-caused to a `ManifestWriter._write_unconditional` race condition (no generation-check on the retry-exhausted
      fallback path), NOT a defect in this fix's code (a narrow re-run of just those 2 tuples landed cleanly and is what
      closed this todo). Filed as its own issue doc + NOTIFIED via this todo per the data-correctness/cross-repo
      big-finding rule: `manifestwriter_unconditional_write_race_data_loss_2026_07_13.md`. Evidence: coverage.json
      written to `gs://central-element-323112-honest-coverage/2026-07-13/coverage.json` (09:42 UTC run); manifest row
      counts 7465459→7465500 across the two runs.

## Progress Log

- **2026-07-12 (slot-14 sonnet/high)** — Dispatched to the P3 todo; it's structurally gated on the P1 operator-decision
  todo above, which was still unresolved and undispatchable-but-unmarked (neither todo's first physical line carried a
  `BLOCKED-*` taxonomy token, so both were normal dispatch candidates despite being genuinely non-actionable by a worker
  — same taxonomy-gap class just fixed today in `plans/active/sports_manifest_canonicalisation_2026_06_01.md`). Added
  `BLOCKED-OPERATOR-DECISION` to both the P1 and P3 checkboxes' first lines so neither gets dispatched to a worker again
  until the operator actually decides (a) vs (b). Raised the decision itself via `/blocked` (options + recommendation
  per RULES.md's escalation format) rather than silently re-skipping. Did not implement (a) or (b) myself — that's the
  operator's call per this doc's own "Recommended decision" section. unified-trading-pm@(this commit).
- **2026-07-13 (slot-6, data_engineering, sonnet/high)** — Closed out the final P3 todo: ran a real
  `collect-onchain-perp-batch` for 2026-07-11 across all 4 affected venues, confirmed all 6 live-only tuples now write
  typed `empty_confirmed` rows, and re-ran `measure_honest_coverage.py --asset-group cefi` to confirm Layer-1
  completeness rose 90.4%→93.2% with none of the 6 tuples remaining in the missing list. All 3 todos in this issue doc
  are now done. Discovered + filed a separate cross-cutting finding
  (`manifestwriter_unconditional_write_race_data_loss_2026_07_13.md`) for a `ManifestWriter` race condition that
  silently dropped 2 of the 6 rows on the first pass (root-caused, not a defect in this fix — a narrow re-run closed
  it). No code changes this session (batch run only) — unified-trading-pm@(this commit).
