---
doc_type: issue
title:
  "Pyth oracle_prices manifest seeds expected_unattempted for feeds the collector's static _PYTH_FEEDS dict cannot fetch
  (JTO/RAY/WIF/JUP/USDC)"
summary: >-
  While executing defi_satellite_ao_dispatch_batch3-006 (C6 Pyth oracle_prices historical backfill), found the
  market-data-tick-defi manifest carries a newer PYTH-SOLANA:SPOT_PAIR:{SYM}-USD instrument_id family (seeded
  2026-08-01, 9 pairs incl. JTO/RAY/WIF/JUP/USDC) that is 100% expected_unattempted and structurally unsatisfiable — the
  collector's static _PYTH_FEEDS dict only has Hermes feed-ids for 7 symbols (SOL/BTC/ETH/JitoSOL/mSOL/bSOL/INF), none
  of which include JTO/RAY/WIF/JUP, and even the 4 overlapping symbols write under a DIFFERENT instrument_id key than
  the seeder expects. UPDATE 2026-08-03 (slot-11): the SAME IS PYTH-SOLANA catalogue is ALSO causing an ACTIVE
  REGRESSION — BTC/ETH/INF oracle_prices real captures stopped dead on 2026-07-19 (the exact day IS started publishing
  this catalogue) because `_filter_pyth_rows_to_is` drops any fetched row not in IS's enumerated set, and that set never
  included BTC/ETH/INF. This blocks C6's own done-when ("zero remaining gap days") from ever being fully true, via TWO
  distinct mechanisms now (seeded-unfetchable rows, AND a live regression dropping previously-working symbols).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, instruments-service]
scope: [engineer]
tags: [defi, oracle-prices, pyth, manifest, expected-unattempted, honest-absence, regression]
related:
  [/plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md, /plans/active/data_completion_defi_2026_07_15.md]
created: 2026-08-03
parent_epic: defi_master
priority: P1
source:
  "worker analysis (slot-12, data_engineering craft) while executing defi_satellite_ao_dispatch_batch3-006 (C6 Pyth
  oracle_prices backfill), 2026-08-03"
assigned_vm: NA
execution_scope: local-only
estimate_class: design
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
context_scope:
  [
    market-tick-data-service/market_tick_data_service/cli/handlers/_oracle_prices_constants.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/oracle_prices_handler.py,
    /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/data_completion_defi_2026_07_15.md,
  ]
---

# Pyth oracle_prices manifest seeds expected_unattempted for feeds the collector cannot fetch

## What I found

Checking the live `market-data-tick-defi-prd-central-element-323112` consolidated manifest
(`_index/availability_index.parquet`, bounded read via `venue=PYTH`, `data_type=oracle_prices` row-group filters — no
whole-corpus walk) plus the in-flight per-VM shard for a backfill I was running, I found the PYTH/SOLANA `oracle_prices`
rows exist under **three coexisting `instrument_id` naming conventions**:

1. `{SYMBOL}_USD` (e.g. `BTC_USD`) — legacy, `captured`, last written 2026-07-23.
2. `{symbol}/usd` (e.g. `btc/usd`) — the CURRENT format `oracle_prices_handler.py`'s `_write_oracle_rows` actually
   writes today (confirmed live from my own backfill VM's shard writes), `captured`/`empty_confirmed`.
3. `PYTH-SOLANA:SPOT_PAIR:{SYM}-USD` (e.g. `PYTH-SOLANA:SPOT_PAIR:JTO-USD`) — a newer family, ALL rows
   `expected_unattempted`, written `2026-08-01T13:02:37Z` (looks seeder-generated, consistent timestamp across every row
   — likely `DefiManifestRecorder.emit_expected_unattempted_for_remaining`, the mechanism this same batch3 plan's C8
   item confirms shipped 2026-08-01).

Family 3 enumerates **9 distinct pairs**: `BSOL-USD`, `JITOSOL-USD`, `JTO-USD`, `JUP-USD`, `MSOL-USD`, `RAY-USD`,
`SOL-USD`, `USDC-USD`, `WIF-USD` — **1485 rows fleet-wide, 999 of them in the 2026-04-15..2026-08-03 window, 100%
`expected_unattempted`, zero `captured`.**

Cross-referencing against `market_tick_data_service/cli/handlers/_oracle_prices_constants.py`'s `_PYTH_FEEDS` static
dict: it has Hermes feed-ids for exactly **7 symbols** — `SOL`, `BTC`, `ETH`, `JitoSOL`, `mSOL`, `bSOL`, `INF` — with
**no entry at all** for `JTO`, `RAY`, `WIF`, or `JUP`. Even for the 4 symbols that DO overlap
(`SOL`/`JitoSOL`/`mSOL`/`bSOL`), the collector writes them under the lowercase-slash `instrument_id` (family 2), never
under the seeder's uppercase-dash `PYTH-SOLANA:SPOT_PAIR:` key (family 3) — so those rows can't reconcile to `captured`
even for symbols the collector genuinely fetches, without an `instrument_id`-naming fix on top of the missing-feed-id
fix.

`load_oracle_feeds_for_date("PYTH", "SOLANA", ...)` (`_instruments_metadata.py:478`) reads IS's `instruments-store-defi`
`venue=PYTH-SOLANA` catalogue to FILTER already-fetched rows to the IS-enumerated `(base,quote)` overlap — it does not
drive what gets fetched (the static feed dict does). This means IS's own PYTH-SOLANA catalogue apparently enumerates a
wider universe (including JTO/RAY/WIF/JUP/USDC) than the collector's static Hermes feed-id list supports, and the
manifest seeder used that wider IS catalogue as its "expected" set.

## UPDATE 2026-08-03 (slot-11): a second, active regression — BTC/ETH/INF real captures stopped 2026-07-19

While verifying C6's done-when after this session's 3 completed Pyth backfill VMs (`mtds-pyth-archive-20260803-074918`,
`pyth-lst-backfill-20260803-081601`, `pyth-lst-backfill-20260803-093121` — all `exit_code=0`, `081601`/`093121` covering
the full `2026-04-15..2026-08-03` C6 window), a bounded manifest read
(`read_availability_index(bucket, columns=[...], filters=[("venue","=","PYTH"),("data_type","=","oracle_prices"), date range])`
— single filtered read, no whole-corpus walk) showed a real, code-caused gap distinct from the family-3 rows documented
above:

- `BTC_USD`/`btc/usd`, `ETH_USD`/`eth/usd`, `INF_USD`/`inf/usd` have **zero** manifest rows (any naming family, any
  `capture_status`) for **17 consecutive days, 2026-07-19 → 2026-08-01** — confirmed even in
  `pyth-lst-backfill- 20260803-093121`'s own per-VM shard (`_index/per_vm/pyth-lst-backfill-20260803-093121.parquet`),
  the FRESHEST, full-window, `exit_code=0` run: `btc/usd`'s rows stop dead at `2026-07-18` and never resume, despite the
  VM processing every date through `2026-08-03`. This is not a backfill-completeness gap (re-running does not fix it) —
  it is the collector actively skipping these 3 symbols on every date in the window.
- `SOL`/`JitoSOL`/`mSOL`/`bSOL` are unaffected (continuous coverage across the same dates) — this is symbol-specific,
  not a wholesale Pyth outage.
- Root cause: `oracle_prices_handler.py`'s `_filter_pyth_rows_to_is` (`:314-354`) restricts every fetched Pyth row to
  the `(base_asset, quote_asset)` set IS enumerates for `venue=PYTH-SOLANA` on that date (`load_oracle_feeds_for_date`,
  `_instruments_metadata.py:478`) — when IS's set is non-empty, only the overlap is kept.
  `instruments-store-defi-prd-central-element-323112/instrument_availability/by_date/day=2026-07-19/.../venue= PYTH-SOLANA/instruments.parquet`
  is the **first ever PYTH-SOLANA blob IS published** (no blob exists for any earlier date — confirmed via `gsutil ls`),
  and its `(base_asset, quote_asset)` set is EXACTLY the 9-pair family-3 catalogue from the finding above:
  `SOL/JITOSOL/MSOL/BSOL/JUP/RAY/WIF/JTO/USDC` — USD. **No BTC, ETH, or INF entry at all.** Before 2026-07-19,
  `load_oracle_feeds_for_date` returned `None` (no blob found) so the filter was a no-op (kept every fetched row, per
  its own documented fallback); from 2026-07-19 onward the filter actively fires and silently drops BTC/ETH/INF even
  though the collector successfully fetches them from Hermes every single date (their static `_PYTH_FEEDS` entries are
  unchanged, 64-hex-valid, and the canonical SOL id in the same dict still resolves live against
  `hermes.pyth.network/v2/price_feeds?query=SOL` — so this is not a feed-id break, purely the IS-catalogue filter).
- This is the SAME root mechanism as the finding above (IS's new PYTH-SOLANA catalogue), just the other side of it: that
  catalogue is simultaneously too NARROW (silently drops 3 previously-working symbols) and too WIDE (seeds 5 unfetchable
  symbols as `expected_unattempted`). Whichever direction the operator rules on below must ALSO restore BTC/ETH/INF to
  IS's enumerated set (or otherwise stop `_filter_pyth_rows_to_is` from dropping statically-supported symbols IS doesn't
  enumerate) — extending `_PYTH_FEEDS` for the 5 new symbols alone does NOT fix this regression.

## Why it matters

- **A permanently-unsatisfiable `expected_unattempted` row is a false "still pending" signal, not a genuine gap awaiting
  a future run.** No VM backfill — including the one this issue's source todo (`defi_satellite_ao_dispatch_batch3-006`,
  C6) dispatched — can ever flip these 999 rows to `captured` as the code is currently written. This pollutes any future
  coverage audit/dashboard with an unfixable-by-backfill entry that looks identical to a genuine, closeable gap.
- **Blocks C6's own done-when from ever being fully true.** That todo's done criterion is "the consolidated manifest
  shows Pyth oracle_prices rows captured (or empty_confirmed) ... with zero remaining gap days" — with family 3 present,
  some rows will always read `expected_unattempted` regardless of how many times a backfill VM runs, until this is
  resolved separately.
- **Data-pipeline correctness heartbeat**: per CLAUDE.md's data-correctness HARD RULE, an audit's issues get fixed in
  full — but resolving this requires a real design/operator call (see below), not a mechanical worker fix, so it is
  filed rather than force-fixed inline.
- **The 2026-08-03 update above is a genuine, ONGOING DATA-LOSS regression, not just a false-pending signal**: real
  BTC/ETH/INF Pyth Hermes prices ARE being fetched successfully every day and then silently discarded by
  `_filter_pyth_rows_to_is` — 17 consecutive days lost so far and counting every day this stays unfixed. This is a big
  finding per CLAUDE.md's findings-triage rule (data-correctness, cross-repo) — flagged for operator attention, not just
  filed passively.

## Recommended decision (operator/design ruling — not a bounded worker fix)

Two genuinely different directions, not mutually exclusive with the naming reconciliation:

1. **Extend the collector**: add real Hermes feed-ids for `JTO/USD`, `RAY/USD`, `WIF/USD`, `JUP/USD`, `USDC/USD` to
   `_PYTH_FEEDS` (verify each id resolves live against `hermes.pyth.network/v2/price_feeds?query=<SYM>` first — this
   file's own inline comments document 2 prior transcription-slip incidents for bSOL/JitoSOL where a
   wrong-but-well-formed id caused a whole-batch 404/400), AND reconcile `_write_oracle_rows`'s output `instrument_id`
   so newly-fetched SOL/JitoSOL/mSOL/bSOL rows are recognizable under (or migrated to) the seeder's
   `PYTH-SOLANA:SPOT_PAIR:{SYM}-USD` key.
2. **OR prune the seeder's input**: if IS's PYTH-SOLANA catalogue enumerating JTO/RAY/WIF/JUP/USDC for `oracle_prices`
   was itself an over-broad seed (these tokens may not actually need on-chain oracle price collection), correct the IS
   catalogue / the seeder's scope back to the 7 symbols the collector supports.
3. **Either way, BTC/ETH/INF MUST be restored to IS's `PYTH-SOLANA` enumerated `(base,quote)` set** (or
   `_filter_pyth_rows_to_is` changed to never drop a symbol the static `_PYTH_FEEDS` dict supports) — direction 1 alone
   (extending the collector for the 5 new symbols) does NOT fix the active BTC/ETH/INF regression; only direction 2
   naturally fixes it (by construction, restoring "the 7 symbols the collector supports" to the catalogue). This is the
   highest-urgency half of the fix (real ongoing data loss vs. a false-pending signal for tokens that were never
   captured).
4. **Either way**: reconcile the pre-existing 3-way `instrument_id` naming split (`{SYM}_USD` / `{sym}/usd` /
   `PYTH-SOLANA:SPOT_PAIR:{SYM}-USD`) onto one canonical form, so a future coverage read doesn't need hand-rolled
   cross-naming normalization (a real risk of a wrong verdict — an early pass at reconciling these families in-session
   produced a false "77 gap days" result before the bug was caught, because normalizing `PYTH-SOLANA:SPOT_PAIR:SOL-USD`
   and the real captured `sol/usd` row to the same key let the newer expected_unattempted row's later `written_at`
   incorrectly shadow the genuinely-captured older row in a last-writer-wins merge).

## Todos

- [x] [OPERATOR] P2 → RESOLVED 2026-08-03. **RULED: direction 1 (EXTEND, not prune)** — extend `_PYTH_FEEDS` with real
      Hermes feed-ids for JTO/RAY/WIF/JUP/USDC AND restore BTC/ETH/INF to the IS `PYTH-SOLANA` enumerated set (support
      the full universe; do NOT prune the seeder scope). **Provenance**: main's final ruling on `BLK-7318d847`
      (disposition=final, reported 2026-08-03T14:30:50Z) as relayed by review → main msg #3561 (2026-08-03T17:13Z). The
      ruling never reached this doc because the filer (slot-9) pivoted to an unrelated one-shot CI dispatch and was
      recycled 3× before consuming its own blocked-answer. The primary blocked-answer payload was NOT re-fetchable from
      the live API (item is final→pruned; persisted state shows it only in the operator-gated dedup list + review's
      concern-verdict ledger entry) — so this is encoded as **review-relayed, pending review's pointer to the source
      record**. (repo: unified-trading-pm, decision only)
- [ ] [BACKEND] P2. Per the ruling (EXTEND): add real, LIVE-VERIFIED Hermes feed-ids for JTO/RAY/WIF/JUP/USDC to
      `market-tick-data-service/market_tick_data_service/cli/handlers/_oracle_prices_constants.py` (`_PYTH_FEEDS`) —
      verify each id resolves against `hermes.pyth.network/v2/price_feeds?query=<SYM>` FIRST (this file documents 2
      prior transcription-slip incidents where a well-formed-but-wrong id 404'd a whole batch) — AND reconcile
      `_write_oracle_rows`'s `instrument_id` derivation so newly-fetched SOL/JitoSOL/mSOL/bSOL rows land under (or
      migrate to) the seeder's `PYTH-SOLANA:SPOT_PAIR:{SYM}-USD` key. NOTE: this doc is `execution_scope: local-only`
      (NA) so this todo does not auto-dispatch — the code fix needs a dispatchable (`assigned_vm: planning`) home to
      actually be worked (see Progress Log). (repo: market-tick-data-service)
- [ ] [DATA] P3. Reconcile the 3 coexisting oracle_prices/PYTH `instrument_id` naming conventions onto one canonical
      form so manifest reads don't need hand-rolled normalization to determine true per-feed coverage. (repo:
      market-tick-data-service, unified-api-contracts)
- [ ] [DATA] P1 (DO FIRST — direction-INDEPENDENT, ongoing data loss). Restore BTC/ETH/INF to IS's `PYTH-SOLANA`
      `instrument_availability` enumerated set (or change `_filter_pyth_rows_to_is` to never drop a symbol `_PYTH_FEEDS`
      statically supports). This is MANDATORY under BOTH extend and prune (§"Recommended decision" pt 3), so it does NOT
      depend on the extend-vs-prune ruling and should be fixed IMMEDIATELY / independently — real Pyth Hermes prices for
      these 3 symbols have been fetched-then-silently-discarded every day since 2026-07-19 (15+ days and counting). NOT
      fixed by extending `_PYTH_FEEDS` alone. (repo: instruments-service or market-tick-data-service)

## Progress Log

- 2026-08-03 (slot-12, data_engineering craft): Discovered while verifying `defi_satellite_ao_dispatch_batch3-006`'s
  (C6) done-when after a SPOT backfill VM (`mtds-pyth-archive-20260803-070759`) was preempted mid-run and I re-checked
  the manifest to determine real remaining gap. Filed this issue; C6 itself proceeds on its own achievable scope (the
  7-symbol fetchable universe) with a Progress Log note pointing here for the structurally-separate gap.
- **context-scout 2026-08-03**: populated context_scope (4 entries).
- **2026-08-03 (slot-11, data_engineering craft)**: Re-dispatched onto C6, found all 3 in-flight/relaunched Pyth
  backfill VMs from earlier today (`074918`, `081601`, `093121`) completed cleanly (`EXIT_STATUS=0` each, live-verified
  via `gsutil cat`, not from memory) with `081601`/`093121` covering the full `2026-04-15..2026-08-03` C6 window. Ran a
  bounded manifest read (single `filters=` predicate-pushdown query, no whole-corpus walk) to check C6's own
  zero-remaining-gap-days done-when and found a SECOND, distinct issue beyond the seeded-unfetchable family documented
  above: a real, active regression silently dropping BTC/ETH/INF captures since 2026-07-19 (root-caused to
  `_filter_pyth_rows_to_is` filtering against the same IS PYTH-SOLANA catalogue this issue already covers — full
  evidence + root cause in the "UPDATE 2026-08-03 (slot-11)" section above). Added todo `[DATA] P1` for this regression,
  bumped this doc's frontmatter `priority` to `P1` (ongoing data loss, not just a false-pending signal), and left the
  plan's C6 checkbox **UNFLIPPED** (zero-remaining-gap-days is false for BTC/ETH/INF, independent of the family-3
  issue). Did not attempt an inline fix — both directions in "Recommended decision" above remain gated on the same open
  `[OPERATOR]` ruling; this update only strengthens the evidence for why direction 2 (prune to the 7 fetchable symbols)
  is the cleaner fix, since it fixes both problems at once.
- **2026-08-03 (slot-9, data_engineering craft)**: Re-dispatched onto `defi_satellite_ao_dispatch_batch3-006` (C6) a
  third time (prior slot-11 session appears to have ended without a formal `/blocked` or `/done` — the task simply sat
  `dispatched` and was reassigned). Confirmed the fleet has zero Pyth-named VMs running or queued
  (`gcloud compute instances list` / `operations list` — the 3 backfill VMs slot-11 verified all completed and were
  deleted cleanly, no drift). Re-ran a bounded, filtered manifest read (`venue='PYTH' AND data_type='oracle_prices'`,
  single `read_parquet(...)` predicate-pushdown query via the `run-bounded-analysis.sh` memory-capped wrapper, no
  whole-corpus walk) and confirmed the BTC/ETH/INF regression is unchanged and still live: `BTC_USD`/`ETH_USD`/`INF_USD`
  and `btc/usd`/`eth/usd`/`inf/usd` all still top out at `2026-07-16`/`2026-07-18` respectively with zero rows of any
  `capture_status` since — the gap has now grown to 16+ consecutive days. `_PYTH_FEEDS` (7 symbols) and
  `_filter_pyth_rows_to_is` are both unchanged in code since slot-11's check — no fix has landed. Since this task's own
  done-when ("zero remaining gap days") cannot be met without the still-open `[OPERATOR]` ruling above, and no further
  C6-scoped action is possible from this slot, filed a formal `/blocked` (this issue doc alone was not surfacing in the
  dashboard's blocked queue, which is likely why this task kept silently bouncing between slots instead of visibly
  waiting on the operator) rather than repeating the same discovery a 4th time. Left the plan's C6 checkbox
  **UNFLIPPED** — same rationale as slot-11.
- **2026-08-03 (main agt-1756f6, via review flag msg #3561)**: Review surfaced a process gap — main's final ruling on
  `BLK-7318d847` (direction 1 "extend", reported 14:30:50Z) never reached this doc because slot-9 (the filer) pivoted to
  an unrelated one-shot CI dispatch (agt-1d8016) minutes after filing and was killed/respawned 3× before consuming its
  own blocked-answer; no slot has touched Pyth/`_PYTH_FEEDS` since, so BTC/ETH/INF oracle_prices kept silently dropping
  (now 15+ days). **Propagated the ruling** into the `[OPERATOR] P2` todo above (with explicit provenance — the primary
  blocked-answer payload was not re-fetchable from the live API, so it is encoded as review-relayed pending review's
  pointer to the source record) and resolved `[BACKEND] P2` to the ruled (extend) direction. **Decoupled `[DATA] P1`**
  (the BTC/ETH/INF regression) from the extend-vs-prune gate: restoring those 3 symbols is required under BOTH
  directions (§"Recommended decision" pt 3), so the ongoing data loss can and should be fixed independently/first rather
  than waiting on the extend-vs-prune choice. **Corrected a stale C6 brief**: the backlog task
  `defi_satellite_ao_dispatch_batch3-006` brief still says "launch a SPOT backfill VM", but the 3 Pyth backfill VMs
  already ran to `exit_code=0` completion (slot-11/slot-9 verified live) — another backfill will NOT fix this; the real
  fix is the code change (IS `PYTH-SOLANA` catalogue filter + `_PYTH_FEEDS`), and C6 should only re-dispatch AFTER that
  code fix lands. **Open follow-up (flagged to review/operator)**: this doc is `execution_scope: local-only` (NA) so its
  `[BACKEND]`/`[DATA]` todos are not auto-dispatched — the code fix needs a dispatchable (`assigned_vm: planning`) home;
  did not author a new dispatchable plan unilaterally (plan-destination is operator's call) nor hand-edit the C6 backlog
  task brief (derived from `/plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md`; backlog is not
  hand-editable). Main cannot push code, so shipping the fix itself requires a worker dispatch.
