---
doc_type: plan
title: Sports EXCHANGE_ODDS vs FIXED_ODDS fork — UAC contract fork + GCS migration (split from the sports closeout)
summary: >-
  Self-contained extraction of sports_consolidated_closeout_2026_07_19.md's Track C "EXCHANGE_ODDS vs FIXED_ODDS fork"
  block (line-cap split, 2026-07-25) — the full UAC-contract-fork + GCS-migration sequence splitting the sports `odds`
  instrument_type into EXCHANGE_ODDS (peer-to-peer exchanges) vs FIXED_ODDS (sportsbooks), itself absorbed 2026-07-23
  from the now-archived sports_odds_exchange_fixed_fork_2026_07_18.md. Genuinely sequential (contracts-before-data
  ordering matters) so it gets its own child rather than folding into a mixed-content sibling. Closes a sequencing gap
  the source block left open: the GCS-move step silently assumed the block's own first `[OPERATOR]` mapping-decision
  todo would hold it — it won't, since a non-dispatchable todo first in a `sequential: true` chain does not count as
  "the predecessor." Splits that step into an immediately-dispatchable pass for the 5 already-unambiguous venues plus a
  separate `[OPERATOR]`-gated follow-on for the 3 still-ambiguous ones.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    unified-api-contracts,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    unified-trading-library,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, exchange-odds, fixed-odds, uac-contract-fork, gcs-migration]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_closeout_exchange_fixed_odds_fork_2026_07_25_finalize.md,
    /plans/active/issues/sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md,
    /plans/archive/2026_07/sports_odds_exchange_fixed_fork_2026_07_18.md,
  ]
created: "2026-07-25"
last_updated: "2026-08-02"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 4.5
estimate_calibrated_ai_days: 3.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_odds_venue_enumeration_undercount_predrain_2026_07_27]
gate_on_depends: true
source: >-
  Extracted 2026-07-25 from sports_consolidated_closeout_2026_07_19.md's Track C "EXCHANGE_ODDS vs FIXED_ODDS fork"
  block (line-cap split pass — the parent was over its 1000L hard cap), itself absorbed 2026-07-23 verbatim from the
  now-archived sports_odds_exchange_fixed_fork_2026_07_18.md.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_closeout_exchange_fixed_odds_fork_2026_07_25_finalize.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/sports-data-types-catalog.md,
  ]
---

# Sports EXCHANGE_ODDS vs FIXED_ODDS fork

> **Status corrected 2026-07-26: this plan is `active`** (frontmatter has said so since creation; this banner was stale
> — flip-to-active already happened, the operator review this banner said to wait for is exactly the 2026-07-26 ruling
> recorded in todo 1 below). **`sequential: true`** — the 11 todos below are a REAL ordering chain (mapping confirmed →
> drain → contracts-first → dual-read → GCS move → dependency_checker update → manifest reconcile → cutover → retire
> legacy → codex audit); this now machine-enforces the ordering the source block previously stated only as prose
> (`sports_consolidated_closeout`'s own "Ordering caveat" bullet, which explicitly said the prose was NOT a dispatch
> gate). **Caveat inherited from `task_template.md` §4**: todo 1 was `[OPERATOR]`-tagged and non-dispatchable until
> 2026-07-26 — it did NOT count as "the predecessor" in the sequential chain, so todo 2 (pre-drain) could dispatch
> without waiting on it. That was intentional: pre-drain / contracts-first / dual-read do not need the 3-ambiguous-venue
> mapping resolved (the source block's own words: "non-ambiguous poles may proceed to design without waiting"). **Todo 1
> is now ruled + closed, and todo 6 is now un-gated to `[DATA]`** (2026-07-26) — the sequential chain now runs straight
> through with no operator-tag skip needed.

> **🔴 HARD ORDERING GATE (operator ruling 2026-07-30, wired 2026-08-02) — this plan is now machine-gated on
> `sports_odds_venue_enumeration_undercount_predrain_2026_07_27`** via frontmatter `depends_on` + `gate_on_depends` (set
> `true`). **The legacy `odds` contract retirement MUST NOT run before the venue→class mapping for the 19
> currently-unmapped venues lands.** That doc's 2026-07-29 census measured **292,117 real `data_type=trades` shards /
> 51,291,778 rows across all 19 venues** (BETONLINEAG, UNIBET, BETRIVERS, WILLIAMHILL, CASUMO, SPORT888, CORAL,
> PADDYPOWER, DRAFTKINGS, UNIBET_UK, SKYBET, BETSSON, FANDUEL, VIRGINBET, LIVESCOREBET, BETVICTOR, LADBROKES_UK, BOVADA,
> BETWAY, UNIBET_EU), 100% `captured` — retiring the legacy contract while they are unmapped would **silently orphan all
> 51.3M rows**. Until then this was tracked only as PROSE (the "⛔ GATED" note on the already-executed 3-venue move
> todo, plus that doc's own operator-notify banner) — prose is explicitly NOT a dispatch gate, which is the same class
> of gap already recorded in
> `/plans/archive/issues/mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md`.
>
> **Mechanism (verified against `agent-orchestrator/server/regen_backlog_from_plan.py`)**: the upstream is an
> `assigned_vm: NA` issue doc, so it contributes zero backlog-task ids. `_wire_gate_on_depends_prereqs` explicitly
> disambiguates that case — it reads the upstream FILE's open todos (`_parse_open_todos`, and `plan_files` includes
> `plans/active/issues/*.md`) and, since that doc has 1 genuinely open `[DATA] P0`, holds every task of THIS plan behind
> the derived named prerequisite `gate-upstream-open:sports_odds_venue_enumeration_undercount_predrain_2026_07_27`
> (named prereqs default to blocking when absent). So this is a REAL hold, not a silent no-op on a non-ingested
> upstream. **Scope note**: the gate holds the whole plan, which also covers the writer-cutover todo — deliberate, and
> correct: cutting live writers over to `exchange_odds`/`fixed_odds` is equally undefined for 19 venues with no class.
> All previously-executed todos are already `[x]` and unaffected.

## Todos

- [x] ✅ [DATA] P0. **RETAGGED 2026-07-28 (stale-tag audit — decision already ruled + adjacent code fix already shipped,
      `[OPERATOR]` never removed).** Confirm the ambiguous EXCHANGE_ODDS/FIXED_ODDS venue→class mapping for the 3
      still-unresolved venues: bare `BETFAIR` (33 rows), `ODDS_API` (33 rows, an aggregator fitting neither class), and
      `PINNACLE` (32,616 rows — sportsbook by mechanism, but UAC models it `PINNACLE_AS_LINE` in `_SNAPSHOT_VENUES`, so
      confirm FIXED_ODDS vs a PINNACLE_AS_LINE special case).** The non-ambiguous poles are already resolved and do not
      wait on this: EXCHANGE_ODDS = `BETFAIR_EX_UK`/`BETFAIR_EX_EU`/`SMARKETS`/`MATCHBOOK`; FIXED_ODDS =
      `BETFAIR_SB_UK`/`BETMGM`. (repo: unified-trading-pm, decision record). **Done when**: this todo's own text records
      the operator's ruling for all 3 venues (a class or an explicit special case per venue). ✅ **RULING
      (2026-07-26):** - **bare `BETFAIR` (33 rows) → EXCHANGE_ODDS.** Every existing registry already treats the bare
      umbrella key as the exchange product (`venue_constants.py:180` `SPORTS_EXCHANGE_VENUES`; `betfair_ws.py`'s own
      docstring calls it "umbrella exchange venue used by execution + reference"; `bookmaker_registry.py` categorizes it
      `EXCHANGE`). The 33 rows are dead legacy writes from a since-fixed structural bug
      (`plans/archive/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md:252,260`, fixed `mtds@accd8aa4`
      2026-07-20, regression test asserts bare BETFAIR is out of scope going forward) — not an ongoing pattern. -
      **`ODDS_API` (33 rows) → FIXED_ODDS.** The Odds API exclusively aggregates fixed-price sportsbook quotes (never
      exchange/peer-to-peer prices — Betfair Exchange has its own dedicated channel), and existing test fixtures already
      assume this split (`unified-api-contracts/tests/unit/test_mvp_scope.py`, multiple
      `is_mvp("sports",       "ODDS_API", "FIXED_ODDS", ...)` calls). `ODDS_API` remains a legitimate real venue for
      `markets`/`outcomes`/ `settlements` going forward — only these 33 legacy `odds`-type rows are in scope for this
      migration. **Cross-checked 2026-07-27** (`mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md` Phase 0-4, which
      fixed a genuine, DIFFERENT `venue=ODDS_API` conflation in MDPS's `reprocess_sports_odds.py`): this ruling is NOT
      the same bug — `markets`/`outcomes`/`settlements` are genuinely vendor-scoped listing/settlement data with no
      per-bookmaker breakdown to attribute (matches UAC's own `VENUES_BY_ASSET_GROUP["sports"]` registry entry for
      `ODDS_API`, "Multi-bookmaker odds aggregator (raw tick data source)" — see
      `/codex/02-data/venue-availability.md`), unlike the fixed bug (a manifest row for data that DID already carry a
      real per-row `bookmaker_key`, just never read). This ruling stands. **Before dispatching the pending "move these 3
      venues" todo below**, re-verify against
      `plans/active/issues/sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md` (P0, open as of this note) —
      that doc found the live `instrument_type=odds` population is far larger (~27 venues, 54.8M rows) than this doc's
      8-venue/561,260-row scope and gates the move todos until reconciled. - **`PINNACLE` (32,616 rows) → FIXED_ODDS, no
      special case.** `PINNACLE_AS_LINE` (`_sports_prediction_contracts.py:       213,248`) is an orthogonal
      schema-column tag (which venues populate the optional `max_bet` column on `SPORTS_ODDS_SNAPSHOT`) — it operates at
      a different layer than the `EXCHANGE_ODDS`/`FIXED_ODDS` `InstrumentType` split (`_instrument_enums.py:95-109`
      documents these as separate layers) and does not conflict with it. PINNACLE is already classified FIXED_ODDS
      everywhere else in the codebase (`venue_constants.py:184,500` `SPORTS_BOOKMAKER_API_VENUES`;
      `bookmaker_registry.py` `BOOKMAKER_API`; `system-integration-tests/.../test_instrument_alignment.py:240-241`
      asserts `"FIXED_ODDS" in       venue_types["PINNACLE"]`). - **Adjacent bug found + fixed while investigating (not
      one of the 3 target venues, findings-triage "adjacent" fix)**: `venue_constants.py:180`'s `SPORTS_EXCHANGE_VENUES`
      incorrectly included `BETFAIR_SB_UK` — the Sportsbook, contradicting this same plan's own already-resolved pole
      (`BETFAIR_SB_UK` → FIXED_ODDS, line above) and its own name ("SB" = Sportsbook). Fixed 2026-07-26: moved
      `BETFAIR_SB_UK` from `SPORTS_EXCHANGE_VENUES` to `SPORTS_BOOKMAKER_WEB_VENUES` (alongside `BETMGM`, its correct
      peer) in `unified-api-contracts/unified_api_contracts/registry/venue_constants.py`. This also corrects its
      fee-model/capability/alpha-profile classification (was incorrectly COMMISSION/SPORTS_EXCHANGE/ALPHA_SEEKING, now
      correctly matches BETMGM's bookmaker classification). No test asserted the old (wrong) classification; existing
      tests iterate the sets rather than hardcode membership. `quality-gates.sh` re-run green post-fix.
- [x] ✅ [DATA] P0. **Pre-drain the sports odds writers before any GCS object move.** `odds` (pre-fork instrument_type,
      561,260 rows) is written live — stop all sports odds-writing jobs both clouds and snapshot first. (repo:
      deployment-service / market-data-processing-service). **Done when**: a corpus-wide check confirms zero sports
      odds-writing jobs are running in either cloud, and the pre-drain snapshot object is recorded (path + row count).
      ✅ **DONE 2026-07-27:** GCP: found + stopped `mtds-backfill-sports-odds-3leagues-1` (project
      `central-element-323112`, zone `asia-northeast1-c`) — was `RUNNING` but stale (heartbeat + run.log both idle
      ~17.6h, every shard failing 401 Unauthorized from The Odds API, likely an expired/invalid key — flagged
      separately, not fixed here since credential rotation is out of this todo's scope).
      `gcloud compute instances     stop` (not delete — reversible), now `TERMINATED`. Corpus-wide re-check
      (`name~"sports"` OR `name~"odds"`, `status=RUNNING`) returns empty. AWS (`ap-northeast-1`, project
      `427895769566`): zero instances tagged `mtds-sports-odds-*` at any state, and the full running/pending list has
      only the two agent-orchestrator VMs — clean, nothing to stop. Pre-drain snapshot: byte-verified round-trip copy of
      the live sports availability index to
      `gs://market-data-tick-sports-prd-central-element-323112/_index/snapshots/pre_odds_predrain_exchange_fixed_fork_2026_07_27_20260727T004717Z.parquet`
      (10,367,527 bytes). **Row count, measured**: 295,921 manifest entries / 54,835,957 summed `row_count` across
      `instrument_type` `odds`+`ODDS` (both casings, unfiltered by date/venue) — materially higher than this todo's own
      "561,260 rows" figure and spanning ~27 venues vs. the plan's 8-venue mapping. Filed as
      `/plans/active/issues/sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md` (P0, operator-notify) —
      **read that doc before dispatching the two "Move the GCS objects" todos below**, since their current venue list
      may be incomplete.
- [x] ✅ [DATA] P1. **Add UAC contract entries for EXCHANGE_ODDS/FIXED_ODDS BEFORE touching data** (contracts-first,
      deliberately — manifest-first previously caused the tradfi CME manifest↔disk↔registry divergence, repaired
      `@bd115230`, must not repeat). Keep the legacy `odds` contract entry live for the dual-read window. (repo:
      unified-api-contracts). **Done when**: both EXCHANGE_ODDS and FIXED_ODDS contract entries exist in UAC alongside
      the still-live legacy `odds` entry. ✅ **DONE 2026-07-27 — `unified-api-contracts@4b28b340`:** registered
      `CONTRACT_REGISTRY[("sports", "exchange_odds", "trades")]` = `SPORTS_EXCHANGE_ODDS_TRADES` and
      `[("sports", "fixed_odds", "trades")]` = `SPORTS_FIXED_ODDS_TRADES` in `_sports_prediction_contracts.py`,
      re-exported via `contracts.py`, both sharing `SPORTS_ODDS_TRADES`'s row schema (frozen `ColumnSpec`/
      `SchemaContract` — the fork splits the instrument_type partition, not the columns). Legacy
      `("sports", "odds", "trades")` stays registered unchanged. **Adjacent fix (findings-triage, same commit)**:
      `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE[("sports", "fixed_odds")]` in `market_data_categories.py` was missing
      `"trades"` (its `exchange_odds` sibling already had it) — without this the new `fixed_odds/trades` registry entry
      would have failed the existing `test_every_sports_odds_family_contract_registry_entry_is_matrix_reachable`
      reachability sweep; added `"trades"` to that frozenset. New unit tests added in
      `test_sports_prediction_contracts.py` (registration, lookup, shared- schema, sample-dataframe validation for both
      new entries; legacy-entry-still-present regression). Full `quality-gates.sh` green (sentinel = `4b28b340`).
- [x] ✅ [DATA] P1. **Dual-read `odds` + `EXCHANGE_ODDS`/`FIXED_ODDS` in `lookup_contract` during the migration window;
      add a UAC unit test covering both paths.** (repo: unified-api-contracts). **Done when**: the new unit test passes
      for both the legacy `odds` path and the new EXCHANGE_ODDS/FIXED_ODDS paths. ✅ **DONE 2026-07-27 —
      `unified-api-contracts@39d8440b`:** only `("sports", "exchange_odds"/"fixed_odds", "trades")` has its own
      `CONTRACT_REGISTRY` entry (todo 3) — every other sports odds `data_type` (`sports_odds_snapshot`,
      `sports_odds_movement`, `sports_arbitrage`, ...) is still registered only under the legacy `odds` instrument_type.
      Added a new resolution step 5 to `lookup_contract` (`unified_api_contracts/internal/schemas/contracts.py`): for
      `asset_group == "sports"` and `instrument_type` in `{"exchange_odds", "fixed_odds"}`, on a registry miss fall back
      to `CONTRACT_REGISTRY[(asset_group, "odds", data_type)]` — safe because the fork shares
      `SPORTS_ODDS_TRADES.columns` by reference (row schema identical, only the partition key differs). New unit tests
      in `test_sports_prediction_contracts.py`: legacy `odds` path still resolves directly; the fork-specific `trades`
      entries still win when they exist; `exchange_odds`/`fixed_odds` + `sports_odds_snapshot` dual-reads to the legacy
      `SPORTS_ODDS_SNAPSHOT` contract via both new instrument_types; the fallback is sports-scoped only (a non-sports
      asset_group with the same instrument_type/data_type still raises `SchemaContractNotFoundError`). Full
      `quality-gates.sh` green (sentinel = `39282596`).
- [x] ✅ [DATA] P1. **Move the `instrument_type=odds/` GCS objects for the 5 already-unambiguous venues ONLY**
      (`BETFAIR_EX_UK`, `BETFAIR_EX_EU`, `SMARKETS`, `MATCHBOOK` → `exchange_odds/`; `BETFAIR_SB_UK`, `BETMGM` →
      `fixed_odds/`) via UTL `gcs_copy_object`/`gcs_delete_object` (never subprocess gsutil); snapshot → move →
      independent re-read count; idempotent + resumable. **Self-justified, not `[OPERATOR]`-gated**: mirrors the same
      snapshot-then-copy-then-delete pattern this doc family already ships without an operator tag (K1/K2, the sports
      league_id relocation) — reversible via the snapshot, and scoped only to the venues whose class is already decided.
      **Excludes** the 3 still-ambiguous venues (see the follow-on todo below). (repo: instruments-service /
      market-data-processing-service). **Done when**: an independent re-read count of the moved objects matches the
      pre-move snapshot count for exactly these 5 venues, with 0 objects lost. ✅ **DONE 2026-07-27 —
      `market-tick-data-service@cee67ac0`:** before executing, read
      `issues/sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md` (P0, open) per this plan's own todo-2
      pointer and confirmed none of these 6 venues (title says "5", the venue list itself names 6) are among the ~19
      unmapped venues that doc's banner protects against — added a PARTIAL RECONCILIATION section to that doc recording
      this (doc stays open for the other venues). Wrote
      `market-tick-data-service/scripts/sports/exchange_fixed_odds_fork/move_odds_unambiguous_venues_2026_07_27.py`
      (snapshot/migrate/verify modes, manifest-derived enumeration — no live GCS walk, no per-row content rewrite since
      `instrument_type`/`data_type` are pure partition keys not row-content columns per `SPORTS_ODDS_TRADES.columns`).
      Real live scope (manifest-measured, not the plan's stale 561,260/32,616 figures): **44,525 shards / 12,778,825
      rows**, all currently `instrument_type=ODDS/data_type=TRADES` (uppercase) on disk — confirmed fresh soft-delete
      retention = 604800s (qualifies for self-authorized delete per delete-safety-protocol §3a path (c)). Snapshot
      phase: 44,525/44,525 sources confirmed on disk, 0 target collisions. Migrate phase (real PROD write, `--confirm`):
      **44,525 copied, 44,525 deleted, 0 FAIL** — server-side `gcs_copy_object` rewrite to lowercase
      `instrument_type=exchange_odds`/`fixed_odds`, `data_type=trades` (matches the UAC contract keys shipped in todo
      3 + the final sports casing doctrine), each copy verified (crc32c+size match) before its source was deleted.
      Independent re-read verification (separate `verify` pass, fresh describes): **target OK=44,525 MISSING=0
      MISMATCH=0, source objects still present=0** — exactly this todo's done-when. **Adjacent finding** (out of this
      todo's scope, not fixed here): a pre-existing, manifest-UNREGISTERED lowercase
      `instrument_type=odds/data_type=trades` duplicate also exists on disk for these 6 venues (residue of the
      now-superseded K1/K2 UPPER-casing migration, which copied but never deleted) — left untouched; recorded as an
      addendum on `sports_consolidated_closeout_2026_07_19.md`'s open K1/K2-revert todo (Step 3) since it's already
      tracked there.
- [x] ✅ [DATA] P1. **⛔ GATED 2026-07-27 — do not dispatch without re-reading
      `plans/active/issues/sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md` (P0, open as of this note)
      FIRST** — that doc found the live `instrument_type=odds` population (~27 venues, 54.8M rows) is far larger than
      this plan's 8-venue/561,260-row scope and explicitly blocks this exact todo pending reconciliation. **Now that the
      mapping todo above is ruled (2026-07-26: bare `BETFAIR`→EXCHANGE_ODDS, `ODDS_API`→FIXED_ODDS,
      `PINNACLE`→FIXED_ODDS), move those 3 venues' GCS objects the same way** (same snapshot → move → independent
      re-read count pattern as the unambiguous-venue todo above: `BETFAIR`→`exchange_odds/`; `ODDS_API`,
      `PINNACLE`→`fixed_odds/`). **Un-gated from `[OPERATOR]` to `[DATA]` 2026-07-26** — it was `[OPERATOR]`-tagged only
      because it couldn't execute correctly until the mapping decision landed; that decision is now recorded above, so
      this is a normal bounded, dispatchable data-move with a determinable done-when, no further human judgment call
      required. Via UTL `gcs_copy_object`/`gcs_delete_object` (never subprocess gsutil). (repo:
      market-data-processing-service / instruments-service). **Done when**: the same re-read-count check passes for all
      3 previously-ambiguous venues once moved, citing the operator's ruling from the mapping todo above, with 0 objects
      lost. ✅ **DONE 2026-07-27 — `market-tick-data-service@2d0a7dc6`:** re-read the GATED doc FIRST per this todo's
      own banner, then re-measured live scope (manifest-derived, no GCS walk) for these 3 specific venues before
      executing. Real live scope under `instrument_type=ODDS/data_type=TRADES`: **bare `BETFAIR` = 0 shards/0 rows**
      (confirmed the venue key does not appear anywhere in the manifest's 31 distinct venues — consistent with the
      mapping todo's own text that the 33 legacy rows were dead writes from a since-fixed bug, `mtds@accd8aa4`
      2026-07-20); **`ODDS_API` = 0 shards/0 rows under `odds`** (the venue key exists in the manifest, but only for
      other instrument_types — markets/outcomes/settlements — none of which are in this fork's scope); **`PINNACLE` =
      15,570 shards / 4,887,512 summed row_count** (uppercase `ODDS`/`TRADES` on disk), matching the undercount issue
      doc's own live PINNACLE figure, not the plan's stale "32,616 rows" citation. **This resolves the GATED banner's
      concern for these 3 venues specifically**: none of the 3 are among the undercount doc's ~19 unmapped-venue list,
      so this move does not create the orphaning risk that doc's banner describes (the doc stays open for those other
      ~19 venues — untouched by this todo). Wrote
      `market-tick-data-service/scripts/sports/exchange_fixed_odds_fork/move_odds_ambiguous_venues_2026_07_27.py` (same
      snapshot/migrate/verify pattern as todo 5's tool). Snapshot: 15,570/15,570 sources confirmed on disk, 0 target
      collisions, fresh soft-delete retention = 604800s (qualifies for self-authorized delete per delete-safety-protocol
      §3a path (c)). Migrate (real PROD write, `--confirm`): **15,570 copied, 15,570 deleted, 0 FAIL** — server-side
      `gcs_copy_object` rewrite to lowercase `instrument_type=fixed_odds`/`data_type=trades` for PINNACLE
      (BETFAIR/ODDS_API had 0 shards to move). Independent re-read verification (separate `verify` pass, fresh
      describes): **target OK=15,570 MISSING=0 MISMATCH=0, source objects still present=0** — exactly this todo's
      done-when. Added a corresponding note to `sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md`
      confirming these 3 venues are not among that doc's ~19 unmapped-venue list (doc stays open for those).
- [x] ✅ [DATA] P1. **Update MDPS `dependency_checker`'s hive-token matcher for the new instrument_type partitions** —
      confirm no consumer of the legacy `odds` hive token goes orphaned. (repo: market-data-processing-service). **Done
      when**: a `dependency_checker` run against the post-move bucket state shows 0 orphaned consumers of the legacy
      `odds` hive token. ✅ **DONE 2026-07-27 — `market-data-processing-service@0814424`:** investigated every caller of
      `check_upstream_data_per_shard` (the one function with an `instrument_type` hive-token matcher) plus the sports
      raw_tick_data scanner (`orchestration_scanner.py`) and the date-level `check_dependencies` gate. Found: (1)
      `check_upstream_data_per_shard`'s `instrument_type` param is a free string, matched as
      `instrument_type={instrument_type}/` — never hardcoded to the legacy `odds`/`ODDS` value; (2) its only production
      caller (`process_handler.py::_filter_shards_by_per_shard_check`) passes `instrument_type=None` ("not known at
      handler level"), so it doesn't discriminate by instrument_type at all; (3) the sports scanner filters by
      `data_type=` only (`_list_instrument_files`), also instrument_type-agnostic; (4) `check_dependencies`'s SPORTS
      gate checks only the date-level `raw_tick_data/by_date/day={date}/` prefix, no instrument_type token.
      **Conclusion: no production code hardcodes the legacy `odds` hive token anywhere in MDPS's dependency-gating path,
      so no code change was required** — the matcher was already generic. Verified live against the post-move bucket
      state: ran `check_dependencies(date, asset_group='sports')` — both required deps (`market-tick-data-service`,
      `instruments-service`) report `available=True`; ran
      `check_upstream_data_per_shard(..., instrument_type='fixed_odds',     data_type='trades')` directly for a migrated
      PINNACLE shard — returns `True` (matcher correctly finds the new partition with zero code changes). Added 3
      regression tests to `tests/unit/test_dependency_checker_sports_prediction.py` (new class
      `TestCheckUpstreamDataPerShardExchangeFixedOdds`) locking in the matcher finds `exchange_odds`/`fixed_odds` shards
      and that a legacy-only `ODDS`/`TRADES` shard does NOT satisfy a `fixed_odds` request post-cutover (exclusivity
      guard) — so a future refactor reintroducing a hardcoded `odds` literal would be caught. **Adjacent finding, out of
      this todo's scope**: while probing the post-move bucket state directly, found 2 manifest-UNREGISTERED legacy
      `ODDS`/`TRADES` objects for PINNACLE under raw (non-canonical) `league_id` values (`CHAMPIONSHIP`,
      `PREMIER_LEAGUE`) that the manifest-driven move tool could not have enumerated — this is the already-tracked
      defect class in `sports_league_id_namespace_migration_2026_07_20.md` (not new), recorded there as an addendum
      rather than fixed here (single-walk discipline: not re-running a live GCS walk to chase 2 objects).
- [x] ✅ [DATA] P1. **Reconcile the availability manifest to the new partitions LAST, only after the unambiguous-venue
      GCS move + dual-read above are proven.** Verify the shard atom is identical across writer/manifest/status/gate.
      (repo: instruments-service / unified-trading-library). **Done when**: a cross-surface shard-atom check
      (`/codex/02-data/availability-manifest-and-data-status.md`'s own definition) passes for the new partitions. ✅
      **DONE 2026-07-27 — `market-tick-data-service@bc84f6a4`:** todos 5/6's move tools are pure GCS object operations
      (`gcs_copy_object`/`gcs_delete_object`/`gcs_describe_object` only — confirmed by inspection, neither ever calls
      `ManifestWriter`/`record_captured`), so the live manifest still carried 60,095 stale `captured` rows at the OLD
      key (`instrument_type=ODDS`, `data_type=TRADES`) for the 7 migrated venues while the NEW key
      (`instrument_type=exchange_odds`/`fixed_odds`, `data_type=trades`) had zero rows — confirmed live via
      `read_availability_index` before touching anything (manifest-only read, no GCS listing; single-walk discipline).
      Per the codex SSOT's Multi-axis-correction banner, sports shard atom =
      `(asset_group=sports, venue, data_type, league_id, day)` — `instrument_type` is a row-level display column, NOT a
      shard axis — but because `data_type` also changed casing (`TRADES`→`trades`) as part of the same move, the old and
      new keys are genuinely different shard atoms (case-sensitive), so this was a real REMOVE-old-atom + ADD-new-atom
      reconcile, not an in-place update. Wrote
      `market-tick-data-service/scripts/sports/exchange_fixed_odds_fork/manifest_reconcile_2026_07_27.py` mirroring
      `league_id_relocation/manifest_swap_2026_07_22.py`'s REMOVE-then-ADD CAS pattern, deriving the ADD/REMOVE plan
      directly from the live manifest (the move tools left no durable report artifact — a saved-report-driven plan
      wasn't available here). Executed `--confirm-prod-write`: mandatory pre-write snapshot
      (`gs://market-data-tick-sports-prd-central-element-323112/_index/snapshots/pre_exchange_fixed_odds_manifest_reconcile_2026_07_27_20260727T185659Z.parquet`,
      verified round-trip) → CAS REMOVE 60,095 stale rows → ADD 60,095 rows at the new lowercase key (same
      date/venue/league_id/row_count) via `ManifestWriter.record_captured` → in-script VERIFY PASSED
      (`stale_remaining=0 new_present=60,095 new_missing=0 new_mismatched=0`). **Independent re-read** (separate
      process, fresh `read_availability_index` call): confirms 0 rows remain at the old key for all 7 venues and exactly
      the expected per-venue row_count at the new key (BETFAIR_EX_EU 2,386,948; BETFAIR_EX_UK 2,407,423; BETFAIR_SB_UK
      1,073,017; BETMGM 10,890; MATCHBOOK 5,786,903; PINNACLE 4,887,512; SMARKETS 1,113,644 — exactly matching the
      pre-reconcile old-key totals) — total manifest row count unchanged (516,204 before and after, as expected for a
      REMOVE=ADD swap of equal size). **Gate surface**: already verified generic in todo 6
      (`check_upstream_data_per_shard`'s `instrument_type` param is a free string with no hardcoded legacy `odds` token;
      regression tests lock this in). **Writer surface**: unaffected by construction — any future writer (todo 8's
      live-writer cutover) using `record_captured` with `data_type=trades` lands at the identical shard atom regardless
      of which of the three `instrument_type` values it passes, since `instrument_type` isn't part of the atom. **Status
      surface checked, no fix needed**: grepped deployment-api's sports data-status code for hardcoded `odds`/`ODDS`
      instrument_type enumerations; the one hit (`_SPORTS_DATA_TYPE_TO_INSTRUMENT_TYPE["trades"] = "odds"` in
      `data_status_drilldown/_schema.py`) is UI schema-lookup plumbing, not a coverage/display filter — it resolves to
      the legacy `odds` UAC contract for `data_type=trades` clicks, which correctly reaches the shared
      `SPORTS_ODDS_TRADES` schema for exchange_odds/fixed_odds rows too via todo 4's dual-read fallback (same columns by
      design), so this remains functionally correct and was left untouched (no defect to fix). `quality-gates.sh` full
      green pre- and post-commit (sentinel matched HEAD both times).
- [ ] [DATA] P2. **Cut the live sports odds writers over to the new instrument_types and un-drain** (reverse of the
      pre-drain todo above). (repo: market-data-processing-service / deployment-service). **Done when**: a fresh live
      write is observed landing under the new instrument_types and the drain flag is confirmed lifted.
- [ ] [DATA] P2. **⛔ HARD-GATED (2026-08-02) on the 19-venue venue→class mapping — see this plan's HARD ORDERING GATE
      banner above.** Machine-held via frontmatter
      `depends_on:     [sports_odds_venue_enumeration_undercount_predrain_2026_07_27]` + `gate_on_depends`, so this can
      no longer dispatch while that doc's `[DATA] P0` mapping todo is open. **Retire the legacy `odds` contract entry +
      the dual-read path once no object/manifest row remains under `odds`** (requires the 3-venue move above to have
      landed — it has, 2026-07-27 — AND all 19 remaining venues to be classified + moved) **and a full corpus re-read
      confirms parity.** (repo: unified-api-contracts). **Done when**: a corpus-wide census confirms 0 remaining
      objects/manifest rows carrying the legacy `odds` instrument_type value **across every venue, not just the 9
      already migrated**, and the dual-read code path is deleted.
- [ ] [REVIEW] P2. **Post-phase codex audit**: update `/codex/02-data/availability-manifest-and-data-status.md` + the
      sports canonical-naming codex doc with the new instrument_types + migration order. (repo: unified-trading-pm).
      **Done when**: both named codex docs cite EXCHANGE_ODDS/FIXED_ODDS and the migration ordering used.

      **DISPATCHED PREMATURELY 2026-07-31T15:38Z (slot 14) — declined, still genuinely blocked.** This plan's own
                              banner states the intended chain ends `... → cutover → retire legacy → codex audit`, but both predecessors
                              are still `[ ]` open at dispatch time: the "cut the live sports odds writers over" todo (2 above) and the
                              "retire the legacy `odds` contract entry" todo (1 above). Writing the codex "migration ordering used" section
                              now would describe an ordering that hasn't actually finished executing yet. This is the SAME `sequential: true`
                              dispatch-order gap already tracked in
                              `/plans/archive/issues/mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md` (now confirmed across
                              4 independent plans — mtds prediction-lane, mdps tradfi ohlcv, and now this sports fork) — added as further
                              corroborating evidence there rather than re-diagnosing here. Declined to write the codex update prematurely; no
                              code shipped.

## Codex SSOTs

`/codex/02-data/availability-manifest-and-data-status.md`, `/codex/02-data/sports-data-types-catalog.md`,
`/codex/05-infrastructure/gcs-object-operations.md`. Plan↔codex drift is review-blocking.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **2026-08-02 (operator ruling 2026-07-30, executed)**: wired the hard ordering gate on the legacy-contract retirement
  — `depends_on: [sports_odds_venue_enumeration_undercount_predrain_2026_07_27]` + `gate_on_depends` set true. Before
  this, the only thing standing between a dispatched worker and retiring the legacy `odds` contract with 51,291,778
  unmapped rows still live was PROSE (an "⛔ GATED" note on an already-completed sibling todo and an operator-notify
  banner on a different doc) — `depends_on` alone is documentation/archival-only per `plans/PLAN_FORMAT.md:242-243`, so
  a real dispatch hold required `gate_on_depends`. Verified the mechanism actually fires for an `assigned_vm: NA`
  upstream (the failure mode recorded in `gate_on_depends_noop_on_local_only_upstream_2026_07_21.md`): the wiring
  function falls back to reading the upstream file's open todos and emits a blocking `gate-upstream-open:<stem>` named
  prerequisite, and that upstream has exactly 1 open `[DATA] P0`. No todo state changed; the previously-executed todos
  stay `[x]`.
