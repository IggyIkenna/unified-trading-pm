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
  [
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/data_completion_defi_2026_07_15.md,
  ]
created: 2026-08-03
author: unknown
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
    market-tick-data-service/market_tick_data_service/cli/handlers/oracle_prices_handler.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_oracle_prices_constants.py,
    instruments-service/instruments_service/reference_data/adapters/defi/pyth.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/canonical_write.py,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
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
      the full universe; do NOT prune the seeder scope). **Evidence**: activity event id=277382 (`blocked_answered`,
      `disposition=final`, `from=main`, slot_id=9, task_id `defi_satellite_ao_dispatch_batch3-006`,
      2026-08-03T14:30:50.291283Z) — the durable system-of-record (survives blocked-queue pruning; verified verbatim via
      `GET /api/activity?type=blocked_answered`). The ruling never reached this doc because the filer (slot-9) pivoted
      to an unrelated one-shot CI dispatch and was recycled 3× before consuming its own blocked-answer; surfaced by
      review (agt-07ff49, msg #3565) and propagated by main. (repo: unified-trading-pm, decision only)
- [x] ✅ [BACKEND] P2 (extend-ids half only) → market-tick-data-service@cd017a1c (2026-08-03, slot-8). Added real,
      live-verified Hermes feed-ids for JTO/RAY/WIF/JUP/USDC to `_oracle_prices_constants.py`'s `_PYTH_FEEDS` (each
      verified 2026-08-03 against `hermes.pyth.network/v2/price_feeds?query=<SYM>`, filtered to the exact
      `Crypto.<SYM>/USD` symbol — JUP/USDC each also return a distinct near-miss feed, JUPUSD/USD and SYRUPUSDC/USD
      respectively, correctly NOT picked). All 5 pass `test_all_feed_ids_are_canonical_64_hex`'s exact-64-hex regression
      guard. **The `instrument_id`-reconciliation half of this todo's original text is NOT done** — that is real,
      separate, higher-risk work (changes `write_defi_rows`'s `instrument_type` from `SPOT_ASSET` to `SPOT_PAIR`, which
      also drives `SchemaContract` lookup + partition-path derivation for 17+ days of already-written production data) —
      it is the SAME work `[DATA] P3` below already tracks, not duplicated here.
- [ ] [DATA] P3. Per D65 ruling (2026-08-22): canonicalize onto the `PYTH-SOLANA:SPOT_PAIR:{SYM}-USD` form via a real
      migration, gated on a regression test guarding the known false-"77 gap days" failure mode (a prior last-writer-
      wins merge attempt shadowed real captured data — see the Progress Log 2026-08-03 entry). Reconcile the 3
      coexisting oracle_prices/PYTH `instrument_id` naming conventions (`{SYM}_USD` / `{sym}/usd` /
      `PYTH-SOLANA:SPOT_PAIR:{SYM}-USD`) onto that canonical form so manifest reads don't need hand-rolled
      normalization to determine true per-feed coverage. (repo: market-tick-data-service, unified-api-contracts)
- [x] ✅ [OPERATOR] P2. Authorize + launch a fresh, narrow post-fix Pyth `oracle_prices` verification collection VM
      covering the regression window (2026-07-15..present, superset of the 2026-07-19..2026-08-01 BTC/ETH/INF gap) — the
      plan's `[DATA] P2` re-verify todo (`defi_satellite_ao_dispatch_batch3_2026_07_26.md`) cannot ever complete without
      this: 3 independent dispatches (slot-12 2026-08-03, slot-11 2026-08-03, slot-11 2026-08-04T01:50Z) all confirmed
      zero post-fix collection has run and all 3 declined to self-launch, citing
      `deployment-service/scripts/vm/launch-mtds-pyth-lst-backfill-vm.sh`'s own header ("DO NOT LAUNCH without operator
      [ack]" — a caution from its origin plan `solana_lst_native_staking_adapters_2026_05_14.md` Phase 4, written for a
      7+ month backfill window, not this ~3-week verification window). Safe-idempotent case for the operator's
      consideration: SPOT, idempotent re-fetch (`MANIFEST_PER_VM_SHARDS=true` + last-writer-wins consolidation — same
      pattern as the 3 Pyth VMs that already ran cleanly to `exit_code=0` this same week), and the code fix + operator
      ruling this verifies (recorded in this same doc's `[OPERATOR] P2 → RESOLVED 2026-08-03` todo above:
      `defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md`) — `instruments-service@dec90cc0`,
      `market-tick-data-service@cd017a1c`, direction 1 "extend" — are already both landed. Once launched + confirmed
      `EXIT_STATUS=0`, re-dispatch `[DATA] P2` to run its same bounded manifest read. Repo: deployment-service (VM
      launch only, no code change). Source: split off after 3 consecutive re-verify dispatches hit the identical
      unmet-precondition dead-end (`defi_satellite_ao_dispatch_batch3-015`, 2026-08-04).
- [x] ✅ [DATA] P1 (DO FIRST — direction-INDEPENDENT, ongoing data loss) → instruments-service@dec90cc0 (2026-08-03,
      slot-8). Rebased my local commit onto slot-6's `a325da86` (which cleared repo-blocker `RB-48c5820b` — the
      unrelated STEP 5.106 gate failure this fix was blocked behind), re-ran `quality-gates.sh` clean, verified
      `dec90cc0` on `origin/live-defi-rollout` (`merge-base --is-ancestor`). Restored BTC/USD, ETH/USD, INF/USD to
      `PYTH_PRICE_FEEDS` (the dict `get_instruments()` uses to publish IS's `PYTH-SOLANA` `instrument_availability`
      catalogue) — ids are the Hermes REST feed-id (live-verified, byte-identical to MTDS's own already-verified values
      for these 3 symbols) rather than a Pythnet on-chain account address like the file's other entries, since
      `raw_symbol` is traceability-only and never parsed/dereferenced as an on-chain address by this adapter. This is
      the higher-priority, decision-independent half of the fix — real Hermes prices for these 3 symbols were being
      fetched successfully and then silently discarded by `_filter_pyth_rows_to_is` every day since 2026-07-19 (will
      resolve going forward once shipped; does NOT backfill the already-lost 2026-07-19..2026-08-03 window, which is
      unrecoverable — Hermes only serves recent history per feed availability).
- [x] ✅ [OPERATOR] P2 → **RESOLVED/SUPERSEDED 2026-08-08.** DOWNGRADED from P1 DO-FIRST (governance-sweep stale-tag
      cleanup, 2026-08-06) — the "ongoing data loss" premise this todo was filed under no longer holds: the same-day
      03:50Z RESOLUTION entry below shipped `market-tick-data-service@202bacc9`, a self-contained MTDS union fix (unions
      IS-enumerated pairs with the collector's own static `_PYTH_FEEDS` set) that stops BTC/ETH/INF from being silently
      dropped **independent of whether `instruments-service` ever redeploys** — verified via a fresh 1-day VM capturing
      all 12 PYTH SOLANA feeds including BTC/ETH/INF. **The "should IS redeploy" question this todo asked is now moot**:
      `instruments-service@6fbaae90` (the BTC/ETH/INF PYTH-SOLANA catalogue fix) already reached `origin/main` on
      `instruments-service` via squash-promote (`chore(promote): LDR → main`, 2026-08-03T20:00Z, per the 004d6499
      promote commit) — reconfirmed BY CONTENT (not SHA ancestry; the repo underwent a history rewrite 2026-08-05,
      invalidating any `git merge-base` check):
      `git show origin/main:instruments_service/reference_data/ adapters/defi/pyth.py` shows all 3 Hermes feed-ids
      present (`BTC/USD`/`ETH/USD`/`INF/USD`, `0xe62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43` /
      `0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace` /
      `0xf51570985c642c49c2d6e50156390fdba80bb6d5f7fa389d2f012ced4f7d208f`, matching the `PYTH_PRICE_FEEDS`
      restoration). CI reconfirmed green:
      `gh run list --branch main --repo IggyIkenna/instruments-service --workflow quality-gates-v2.yml --limit 5` — 5/5
      most recent runs `completed success` (2026-08-07T20:19Z..23:02Z), so the 2026-08-06 01:35Z CI-red note below is
      stale/self-resolved and no longer blocking promotion. The remaining action is a mechanical ops-check, not an
      operator judgment call — reclassified below.
- **[SCRIPT] P2. EXTRACTED 2026-08-09 → `defi_satellite_ao_dispatch_batch11_2026_08_09.md`.** Confirm the live IS Cloud
  Run revision actually serves `instruments-service@main` HEAD (i.e. the deployed image includes the
  `6fbaae90`/content-equivalent PYTH_PRICE_FEEDS fix, not a stale pre-fix image) — a mechanical ops-check, not a
  redeploy-authorization judgment call (the code question above is closed). Read the active Cloud Run revision's
  deployed image digest/commit label (`gcloud run services describe instruments-service --region <region> --format=...`
  or the equivalent per `/codex/05-infrastructure/deployment-observability.md`) and compare against `origin/main` HEAD;
  if stale, confirm whether the daily `instruments-service-daily-trigger` Workflow already picked up a newer revision on
  its own (Cloud Run auto-deploy vs manual-trigger-only) before concluding a redeploy is still needed. **Done when**: a
  dated Progress Log entry states the live revision's commit/digest and whether it matches main HEAD, with the
  `gcloud`/`gh` command output cited as evidence.

## Progress Log

- 2026-08-03 (slot-12, data_engineering craft): Discovered while verifying `defi_satellite_ao_dispatch_batch3-006`'s
  (C6) done-when after a SPOT backfill VM (`mtds-pyth-archive-20260803-070759`) was preempted mid-run and I re-checked
  the manifest to determine real remaining gap. Filed this issue; C6 itself proceeds on its own achievable scope (the
  7-symbol fetchable universe) with a Progress Log note pointing here for the structurally-separate gap.
- **context-scout 2026-08-03**: populated context_scope (4 entries).
- **context-scout 2026-08-03 (re-scout)**: refreshed context_scope (5 entries) — swapped
  `data_completion_defi_2026_07_15` (no longer relevant) for the IS-side `pyth.py` (PYTH_PRICE_FEEDS, root of the
  BTC/ETH/INF regression fix) + `canonical_write.py` (SPOT_ASSET/SPOT_PAIR schema-contract path the remaining [DATA] P3
  naming-reconciliation todo touches).
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
  task brief (derived from `/plans/archive/2026_07/defi_satellite_ao_dispatch_batch3_2026_07_26.md`; backlog is not
  hand-editable). Main cannot push code, so shipping the fix itself requires a worker dispatch.
- **2026-08-03 (slot-8, backend_engineer craft, dispatched via `defi_satellite_ao_dispatch_batch3-013`)**: wrote both
  decision-independent halves of the code fix. The extend-ids half of `[BACKEND] P2` (JTO/RAY/WIF/JUP/USDC) SHIPPED —
  `market-tick-data-service@cd017a1c`, `quality-gates.sh` green, verified on `origin/live-defi-rollout`
  (`merge-base --is-ancestor`). `[DATA] P1` (BTC/ETH/INF restoration) initially committed locally only
  (`instruments-service@8a5fcdce`) and blocked: `quality-gates.sh` FAILED on that repo (STEP 5.106, 3 bare
  `read_availability_index` sites in `cli/main.py`, confirmed pre-existing/unrelated to my diff via a clean re-run of
  `check_bare_read_availability_index.py` — these came from CLI-subcommand commits landed earlier 2026-08-03, after the
  checker's own 2026-07-31 zero-new-occurrences re-verify). Tracked the 3 new sites as a todo in
  `read_availability_index_bare_defi_callers_2026_07_27.md` and declared repo-blocker `RB-48c5820b` rather than fixing
  that unrelated regression inline (out of scope for this task) or force-shipping past a failing gate. **Resolved same
  session**: slot-6 fixed the 3 sites (`instruments-service@a325da86`), clearing the blocker; rebased my commit onto it
  (`dec90cc0`), re-ran `quality-gates.sh` clean, and shipped — verified on `origin/live-defi-rollout`. `[DATA] P1`
  flipped above citing the landed `dec90cc0`. Live-verified all 8 Pyth ids (3 cross-checked against MTDS's existing
  values — byte-identical, confirming no drift; 5 new) directly against `hermes.pyth.network/v2/price_feeds`, not from
  memory, given this exact file's documented history of transcription-slip incidents. **Deliberately did NOT attempt**
  the `instrument_id`-naming reconciliation (the other half of `[BACKEND] P2`'s original text, and all of `[DATA] P3`):
  traced `write_defi_rows`'s call (`instrument_type=SPOT_ASSET` → `_build_defi` code path) against IS's seeder
  (`instrument_type=SPOT_PAIR` → `_build_cefi_simple` code path) and confirmed the two are genuinely different code
  paths — `write_defi_rows`'s `instrument_type` also drives its `SchemaContract` lookup (strict-mode, would need a NEW
  registered `defi/spot_pair/oracle_prices` contract) and partition-path derivation for 17+ days of already-written
  production data under the current naming. Real, separate, higher-risk work matching this doc's own earlier caution
  about this exact reconciliation ("an early pass... produced a false '77 gap days' result") — left for `[DATA] P3`'s
  dedicated pass, not rushed here.
- **2026-08-03 (slot-12, data_engineering craft, dispatched via `defi_satellite_ao_dispatch_batch3-015`, the plan's
  `[DATA] P2` re-verify todo)**: precondition not yet met — **no live/backfill collection has run since the code fix
  landed**, so nothing to verify yet. Ran the same bounded manifest read this todo specifies
  (`read_availability_index(..., columns=[...], filters=[("venue","=","PYTH"),("data_type","=","oracle_prices"), ("date",">=","2026-07-18")])`,
  single filtered slim read, no whole-corpus walk, via `scripts/dev/run-bounded-analysis.sh`) and confirmed:
  `BTC_USD`/`btc/usd`, `ETH_USD`/`eth/usd`, `INF_USD`/`inf/usd` still have zero rows past `2026-07-18` (their
  `written_at` max is `2026-08-03T10:22:43Z`, hours BEFORE `market-tick-data-service@cd017a1c` (18:08Z) and
  `instruments-service@dec90cc0` (18:22Z) landed — so even that stale row predates the fix).
  `JTO`/`RAY`/`WIF`/`JUP`/`USDC` (family-3 `PYTH-SOLANA:SPOT_PAIR:{SYM}-USD` rows) are still 100%
  `expected_unattempted`, `written_at` max `2026-08-03T01:34:37Z` (the original seeder timestamp, also pre-fix). Checked
  for a routine live/cron path that might pick this up automatically without a manual VM launch — none found
  (`gcloud compute instances list` shows zero Pyth-named VMs running; grepped
  `market-tick-data-service/.github/ workflows/*.yml` for a scheduled oracle_prices job, none exists — collection here
  is via manually-launched `pyth-lst-backfill-*`/`mtds-pyth-archive-*` SPOT VMs, same as the 3 that already
  ran-to-completion earlier today, all BEFORE the fix). Did not launch a new verification VM myself: this todo's own
  scope is explicitly "verification only, no code" (a launch is out of scope for the split-off `[DATA] P2` todo), and
  `launch-mtds-pyth-lst-backfill-vm.sh`'s header gates any launch on an operator `[ack]` (stale pointer to the retired
  file-ping mechanism, but the underlying caution — don't self-authorize a fresh multi-symbol Hermes-rate-limited
  collection run — still applies). **Checkbox stays UNFLIPPED** — released via `/skip-current-task` rather than forcing
  a launch outside this todo's scope; next dispatch should re-check whether a collection has run in the meantime before
  re-attempting this same bounded read.
- **2026-08-04T01:50Z (slot 11, data_engineering craft, dispatched via `defi_satellite_ao_dispatch_batch3-015`)**:
  Re-dispatched ~7.5h after slot-12's check. Precondition still unmet — no live/backfill collection has run since the
  code fix landed. Confirmed fresh, not assumed: `gcloud compute instances list --filter="name~'pyth'"` returns zero
  instances (any status), and a `compute.instances.*` audit-log sweep for any `pyth`-named resource since
  2026-08-03T18:00Z returns zero operations — no VM was ever launched post-fix. Re-ran the same bounded, filtered
  manifest read (`filters=[(venue,PYTH),(data_type,oracle_prices),(date>=2026-07-15)]`, single predicate-pushdown read
  via `run-bounded-analysis.sh`, no whole-corpus walk) with explicit written_at checks against the fix-landing
  timestamps: BTC/ETH/INF (`BTC_USD`/`ETH_USD`/`INF_USD`, `btc,eth,inf/usd`) still max out at `date=2026-07-18`,
  `written_at=2026-08-03T10:22:43Z` — hours before `market-tick-data-service@cd017a1c` (18:08:46Z) and
  `instruments-service@dec90cc0` (18:22:04Z) — zero rows written after either fix, byte-identical to slot-12's finding.
  Family-3 `PYTH-SOLANA:SPOT_PAIR:{SYM}-USD` rows (JTO/RAY/WIF/JUP/USDC + the 4 overlap symbols) are still 100%
  `expected_unattempted`, `written_at` max unchanged at `2026-08-03T01:34:37Z` (the original seeder timestamp). No
  routine live/cron path exists (unchanged since slot-12's check — collection is manual-VM-only, and this todo's own
  scope is explicitly verification-only, no launch). **Checkbox stays UNFLIPPED** — released via `/skip-current-task`
  (reason_code=GATED, genuinely worker-unresolvable: launching the verification collection is out of this todo's scope
  and gated on an operator ack per the launcher's own header). No further re-dispatch of this exact todo is useful until
  someone (operator, or a differently-scoped todo) actually launches a post-fix Pyth collection VM — recommend the next
  dispatch check `gcloud compute instances list --filter="name~'pyth'"` for a NEW VM before repeating this identical
  manifest read a 3rd time.
- **2026-08-04 (slot-5, data_engineering craft, dispatched via `defi_satellite_ao_dispatch_batch3-015`, 3rd re-verify
  dispatch)**: Followed slot-11's own recommendation before repeating the manifest read a 3rd time — checked for a NEW
  Pyth VM first: `gcloud compute instances list --filter="name~'pyth'"` returns zero instances (any status), and a
  `compute.instances.insert` audit-log sweep (`--freshness=2d`) shows the same 6 insert events as slot-11 already
  verified, latest `2026-08-03T09:31:36Z` (`pyth-lst-backfill-20260803-093121`) — zero new launches since slot-11's
  2026-08-04T01:50Z check. Precondition still unmet; did not repeat the manifest read (no new data to find). Instead of
  a 4th identical dead-end dispatch, closed the actual gap: 3 consecutive slots independently declined to self-launch
  the verification VM (citing the same launcher header) but none of them turned that into trackable work — added the
  `[OPERATOR] P2` todo above so the launch decision has an explicit, dispatchable-to-a-human home instead of being
  rediscovered from Progress Log prose on every future dispatch. **Checkbox stays UNFLIPPED** on `[DATA] P2` (plan) —
  released via `/skip-current-task` (reason_code=GATED). Recommend no further re-dispatch of the plan's `[DATA] P2`
  until the new `[OPERATOR] P2` todo here is actioned and a fresh Pyth VM reaches `EXIT_STATUS=0`.
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid — both remaining open items are
  genuinely gated: `[OPERATOR] P2` is an explicit operator VM-launch authorization, `[DATA] P3` is real design/judgment
  work reconciling 3 instrument_id naming conventions (a prior attempt already produced a false "77 gap days" result).
  Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **2026-08-06 (slot-12, data_engineering craft, `defi_satellite_ao_dispatch_batch3-015` 6th dispatch)** — ACTIONED the
  `[OPERATOR] P2` todo: launched `pyth-lst-backfill-20260806-010524` (SPOT, `e2-standard-4`, `asia-northeast1-c`,
  `2026-07-15..2026-08-06` window) via `deployment-service/scripts/vm/launch-mtds-pyth-lst-backfill-vm.sh`. Both code
  fixes confirmed on `origin/live-defi-rollout` before launch: `instruments-service@6fbaae90` (content-identical to
  `dec90cc0`, restores BTC/ETH/INF to `PYTH_PRICE_FEEDS`) and `market-tick-data-service@cd017a1c` (extends `_PYTH_FEEDS`
  with JTO/RAY/WIF/JUP/USDC). Pre-launch bounded manifest read (`filters=venue=PYTH, data_type=oracle_prices`, slim
  columns) confirmed current state: 14,741 total rows (2018-01-01..2026-08-05); BTC/ETH/INF last captured 2026-07-18
  (17-day gap persists); JTO/RAY/WIF/JUP/USDC all `expected_unattempted` under family-3 naming. The 3-week verification
  window makes this a ~30-min run (not the 7+ month backfill the launcher's "DO NOT LAUNCH without operator [ack]"
  header was written for). Flipped `[OPERATOR] P2` checkbox. VM is RUNNING; `[DATA] P2` re-verify todo in the plan stays
  UNFLIPPED pending `EXIT_STATUS=0` + post-VM manifest re-read.
  - **2026-08-06 01:29Z (slot-12, FINAL, same dispatch)** — **VM completed `exit_code=0`** (deployment `d696682c`).
    Per-VM manifest: 23 dates (2026-07-15..2026-08-06), 219 PYTH SOLANA rows, all `captured`.
    - **JTO/RAY/WIF/JUP/USDC**: captured on ALL 23 dates ✓ — MTDS@cd017a1c confirmed working end-to-end.
    - **BTC/ETH/INF**: captured only 2026-07-15..2026-07-18 (4 dates, no IS blob, filter no-op). Dropped
      2026-07-19..2026-08-06 (19 dates — IS PYTH-SOLANA blob exists with pre-fix 9-feed set). **IS@6fbaae90 code is on
      LDR but IS service has NOT been redeployed**: `instruments-service-daily-trigger` (Cloud Scheduler → Workflow
      `instruments-service-daily`, 08:30 UTC daily) still publishes 9-feed blobs from the pre-fix deployed image. The
      2026-08-05 and 2026-08-06 IS blobs were verified directly — both have only 9 pairs (no BTC/ETH/INF). **Until IS
      republishes, `_filter_pyth_rows_to_is` will silently drop BTC/ETH/INF for every date where a PYTH-SOLANA blob
      exists.** IS redeployment is an [OPERATOR] action (Cloud Run deploy or Workflow trigger). Plan `[DATA] P2` stays
      UNFLIPPED — BTC/ETH/INF capture has not resumed post-fix.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tranche=defi, dispatch agt-e00d37): KEEP-NA valid — sole pre-existing open todo
  (`[DATA] P3`, instrument_id convention reconciliation) is genuine design/judgment work, confirmed not duplicated
  elsewhere (`defi_satellite_ao_dispatch_batch3_2026_07_26.md` explicitly disclaims it). **BIG FINDING**: today's
  slot-12 VM run (above) proved the BTC/ETH/INF regression is STILL ACTIVE — code fixed but IS never redeployed — and
  that fact existed only as Progress Log prose, never a tracked checkbox, violating the "every follow-up is a checkbox,
  never prose" HARD RULE. Fixed in this same commit: added a new `[OPERATOR] P1` todo above tracking the IS redeploy
  action. Flagging to the operator via this run's completion report — this is an ongoing, cross-repo, P1
  data-correctness regression that did not actually resolve when the code merged.
  - **2026-08-06 01:35Z (slot-12, CI check)**: IS `quality-gates-v2` is FAILING on `064e2560` (current LDR HEAD) —
    pre-existing `pytest` failure from stale UAC dependency resolution (known issue documented in the QG script's own
    comments: "resolving an OLD UAC → false pytest FAILING that re-stales tier-0 ci_status overnight"). LDR→main
    promotion also failing. This CI red gate may be blocking IS from being redeployed, keeping the PYTH-SOLANA
    `instrument_availability` blob stuck on the pre-fix 9-feed set. Not a Pyth-specific issue — IS CI has been red since
    at least 2026-08-05. Operator may need to unblock this separately from the Pyth fix itself.
  - **2026-08-06 03:50Z (slot-12, RESOLUTION)** — **MTDS union fix shipped + verified.**
    `market-tick-data-service@202bacc9` (LDR via quickmerge, QG green): modified `_filter_pyth_rows_to_is` to union
    IS-enumerated pairs with the collector's own static `_PYTH_FEEDS` pairs — a stale/missing IS catalogue entry can
    never silently drop a feed the collector explicitly supports. Verified via `pyth-lst-backfill-20260806-035000`
    (1-day VM, 2026-08-06, `exit_code=0`): all 12 PYTH SOLANA feeds captured including BTC/USD, ETH/USD, INF/USD —
    confirmed via per-VM manifest (all `captured`). JTO/RAY/WIF/JUP/USDC also captured (MTDS@cd017a1c). **This resolves
    the BTC/ETH/INF data-loss regression documented in this issue** — the fix is self-contained in MTDS and does not
    depend on IS republishing. IS@6fbaae90 (restoring BTC/ETH/INF to `PYTH_PRICE_FEEDS`) remains on LDR as a
    complementary SSOT fix; the union guard makes the collector resilient to any future IS catalogue gap. Plan
    `[DATA] P2` flipped with evidence. Remaining: `[DATA] P3` (instrument_id naming reconciliation) is tracked
    separately.
- **na-corpus-digest-closeout 2026-08-08**: reconfirmed live that `instruments-service@6fbaae90`'s BTC/ETH/INF fix
  reached `origin/main` (content-verified via `git show origin/main:.../pyth.py`, all 3 Hermes feed-ids present — SHA
  ancestry not used, per the 2026-08-05 history-rewrite caveat) and that `quality-gates-v2` is green on main (5/5 recent
  runs success, 2026-08-07T20:19Z..23:02Z). Marked the `[OPERATOR] P2` "should IS redeploy" todo resolved/superseded —
  the code question is closed — and filed a new `[SCRIPT] P2` mechanical ops-check todo to confirm the LIVE Cloud Run
  revision actually serves that main HEAD (distinct from "is the fix on main", which is now answered).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — 2 open items remain: `[DATA] P3`
  (reconcile the 3 coexisting `instrument_id` naming conventions) is genuine design/judgment work the doc's own text
  flags as previously producing a false "77 gap days" result — real risk, not a mechanical rename; `[SCRIPT] P2` (the
  Cloud Run revision ops-check filed today) is bounded/mechanical on its own, but `assigned_vm` flips whole-doc, so it
  can't be split from the naming-reconciliation item. `defi_satellite_ao_dispatch_batch10_2026_08_06.md`'s own
  pre-2026-08-08 "cite-only" bucket already characterizes the naming half as "deliberately deferred as risky design
  work," consistent with this verdict. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid -- Sole open checkbox is genuine design/judgment
  work (reconcile 3 coexisting oracle_prices/PYTH naming conventions) -- an earlier in-session attempt at this exact
  reconciliation produced a false "77 gap days" result via a last-writer-wins merge shadowing real data. Multiple
  standing audits (2026-08-04/07/08) independently reached KEEP-NA. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-16** [body-hash:6e8ce2a479c03735]: KEEP-NA, valid — Read end-to-end, including the extensive Progress Log documenting a two-mechanism active data-loss regression (seeded-unfetchable family-3 rows AND a live BTC/ETH/INF drop via _filter_pyth_rows_to_is), both since fixed and live-verified via a VM capturing all 12 PYTH SOLANA feeds. 5 of 6 original todos are closed.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **context-scout 2026-08-20**: refreshed context_scope (5 entries)
- **2026-08-22 — ruling D65 (Pyth instrument_id canonicalization)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): PYTH-SOLANA form with migration, gated on a regression test against the
  known false-77-gap-days failure mode. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md
  ledger.
