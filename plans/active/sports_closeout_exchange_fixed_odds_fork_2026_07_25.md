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
    /plans/archive/2026_07/sports_odds_exchange_fixed_fork_2026_07_18.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
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
depends_on: []
source: >-
  Extracted 2026-07-25 from sports_consolidated_closeout_2026_07_19.md's Track C "EXCHANGE_ODDS vs FIXED_ODDS fork"
  block (line-cap split pass — the parent was over its 1000L hard cap), itself absorbed 2026-07-23 verbatim from the
  now-archived sports_odds_exchange_fixed_fork_2026_07_18.md.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
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

## Todos

- [x] ✅ [OPERATOR] P0. **Confirm the ambiguous EXCHANGE_ODDS/FIXED_ODDS venue→class mapping for the 3 still-unresolved
      venues: bare `BETFAIR` (33 rows), `ODDS_API` (33 rows, an aggregator fitting neither class), and `PINNACLE`
      (32,616 rows — sportsbook by mechanism, but UAC models it `PINNACLE_AS_LINE` in `_SNAPSHOT_VENUES`, so confirm
      FIXED_ODDS vs a PINNACLE_AS_LINE special case).** The non-ambiguous poles are already resolved and do not wait on
      this: EXCHANGE_ODDS = `BETFAIR_EX_UK`/`BETFAIR_EX_EU`/`SMARKETS`/`MATCHBOOK`; FIXED_ODDS =
      `BETFAIR_SB_UK`/`BETMGM`. (repo: unified-trading-pm, decision record). **Done when**: this todo's own text records
      the operator's ruling for all 3 venues (a class or an explicit special case per venue). ✅ **RULING
      (2026-07-26):** - **bare `BETFAIR` (33 rows) → EXCHANGE_ODDS.** Every existing registry already treats the bare
      umbrella key as the exchange product (`venue_constants.py:180` `SPORTS_EXCHANGE_VENUES`; `betfair_ws.py`'s own
      docstring calls it "umbrella exchange venue used by execution + reference"; `bookmaker_registry.py` categorizes it
      `EXCHANGE`). The 33 rows are dead legacy writes from a since-fixed structural bug
      (`plans/active/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md:252,260`, fixed `mtds@accd8aa4`
      2026-07-20, regression test asserts bare BETFAIR is out of scope going forward) — not an ongoing pattern. -
      **`ODDS_API` (33 rows) → FIXED_ODDS.** The Odds API exclusively aggregates fixed-price sportsbook quotes (never
      exchange/peer-to-peer prices — Betfair Exchange has its own dedicated channel), and existing test fixtures already
      assume this split (`unified-api-contracts/tests/unit/test_mvp_scope.py`, multiple
      `is_mvp("sports",       "ODDS_API", "FIXED_ODDS", ...)` calls). `ODDS_API` remains a legitimate real venue for
      `markets`/`outcomes`/ `settlements` going forward — only these 33 legacy `odds`-type rows are in scope for this
      migration. - **`PINNACLE` (32,616 rows) → FIXED_ODDS, no special case.** `PINNACLE_AS_LINE`
      (`_sports_prediction_contracts.py:       213,248`) is an orthogonal schema-column tag (which venues populate the
      optional `max_bet` column on `SPORTS_ODDS_SNAPSHOT`) — it operates at a different layer than the
      `EXCHANGE_ODDS`/`FIXED_ODDS` `InstrumentType` split (`_instrument_enums.py:95-109` documents these as separate
      layers) and does not conflict with it. PINNACLE is already classified FIXED_ODDS everywhere else in the codebase
      (`venue_constants.py:184,500` `SPORTS_BOOKMAKER_API_VENUES`; `bookmaker_registry.py` `BOOKMAKER_API`;
      `system-integration-tests/.../test_instrument_alignment.py:240-241` asserts
      `"FIXED_ODDS" in       venue_types["PINNACLE"]`). - **Adjacent bug found + fixed while investigating (not one of
      the 3 target venues, findings-triage "adjacent" fix)**: `venue_constants.py:180`'s `SPORTS_EXCHANGE_VENUES`
      incorrectly included `BETFAIR_SB_UK` — the Sportsbook, contradicting this same plan's own already-resolved pole
      (`BETFAIR_SB_UK` → FIXED_ODDS, line above) and its own name ("SB" = Sportsbook). Fixed 2026-07-26: moved
      `BETFAIR_SB_UK` from `SPORTS_EXCHANGE_VENUES` to `SPORTS_BOOKMAKER_WEB_VENUES` (alongside `BETMGM`, its correct
      peer) in `unified-api-contracts/unified_api_contracts/registry/venue_constants.py`. This also corrects its
      fee-model/capability/alpha-profile classification (was incorrectly COMMISSION/SPORTS_EXCHANGE/ALPHA_SEEKING, now
      correctly matches BETMGM's bookmaker classification). No test asserted the old (wrong) classification; existing
      tests iterate the sets rather than hardcode membership. `quality-gates.sh` re-run green post-fix.
- [ ] [DATA] P0. **Pre-drain the sports odds writers before any GCS object move.** `odds` (pre-fork instrument_type,
      561,260 rows) is written live — stop all sports odds-writing jobs both clouds and snapshot first. (repo:
      deployment-service / market-data-processing-service). **Done when**: a corpus-wide check confirms zero sports
      odds-writing jobs are running in either cloud, and the pre-drain snapshot object is recorded (path + row count).
- [ ] [DATA] P1. **Add UAC contract entries for EXCHANGE_ODDS/FIXED_ODDS BEFORE touching data** (contracts-first,
      deliberately — manifest-first previously caused the tradfi CME manifest↔disk↔registry divergence, repaired
      `@bd115230`, must not repeat). Keep the legacy `odds` contract entry live for the dual-read window. (repo:
      unified-api-contracts). **Done when**: both EXCHANGE_ODDS and FIXED_ODDS contract entries exist in UAC alongside
      the still-live legacy `odds` entry.
- [ ] [DATA] P1. **Dual-read `odds` + `EXCHANGE_ODDS`/`FIXED_ODDS` in `lookup_contract` during the migration window; add
      a UAC unit test covering both paths.** (repo: unified-api-contracts). **Done when**: the new unit test passes for
      both the legacy `odds` path and the new EXCHANGE_ODDS/FIXED_ODDS paths.
- [ ] [DATA] P1. **Move the `instrument_type=odds/` GCS objects for the 5 already-unambiguous venues ONLY**
      (`BETFAIR_EX_UK`, `BETFAIR_EX_EU`, `SMARKETS`, `MATCHBOOK` → `exchange_odds/`; `BETFAIR_SB_UK`, `BETMGM` →
      `fixed_odds/`) via UTL `gcs_copy_object`/`gcs_delete_object` (never subprocess gsutil); snapshot → move →
      independent re-read count; idempotent + resumable. **Self-justified, not `[OPERATOR]`-gated**: mirrors the same
      snapshot-then-copy-then-delete pattern this doc family already ships without an operator tag (K1/K2, the sports
      league_id relocation) — reversible via the snapshot, and scoped only to the venues whose class is already decided.
      **Excludes** the 3 still-ambiguous venues (see the follow-on todo below). (repo: instruments-service /
      market-data-processing-service). **Done when**: an independent re-read count of the moved objects matches the
      pre-move snapshot count for exactly these 5 venues, with 0 objects lost.
- [ ] [DATA] P1. **Now that the mapping todo above is ruled (2026-07-26: bare `BETFAIR`→EXCHANGE_ODDS,
      `ODDS_API`→FIXED_ODDS, `PINNACLE`→FIXED_ODDS), move those 3 venues' GCS objects the same way** (same snapshot →
      move → independent re-read count pattern as the unambiguous-venue todo above: `BETFAIR`→`exchange_odds/`;
      `ODDS_API`, `PINNACLE`→`fixed_odds/`). **Un-gated from `[OPERATOR]` to `[DATA]` 2026-07-26** — it was
      `[OPERATOR]`-tagged only because it couldn't execute correctly until the mapping decision landed; that decision is
      now recorded above, so this is a normal bounded, dispatchable data-move with a determinable done-when, no further
      human judgment call required. Via UTL `gcs_copy_object`/`gcs_delete_object` (never subprocess gsutil). (repo:
      market-data-processing-service / instruments-service). **Done when**: the same re-read-count check passes for all
      3 previously-ambiguous venues once moved, citing the operator's ruling from the mapping todo above, with 0 objects
      lost.
- [ ] [DATA] P1. **Update MDPS `dependency_checker`'s hive-token matcher for the new instrument_type partitions** —
      confirm no consumer of the legacy `odds` hive token goes orphaned. (repo: market-data-processing-service). **Done
      when**: a `dependency_checker` run against the post-move bucket state shows 0 orphaned consumers of the legacy
      `odds` hive token.
- [ ] [DATA] P1. **Reconcile the availability manifest to the new partitions LAST, only after the unambiguous-venue GCS
      move + dual-read above are proven.** Verify the shard atom is identical across writer/manifest/status/gate. (repo:
      instruments-service / unified-trading-library). **Done when**: a cross-surface shard-atom check
      (`/codex/02-data/availability-manifest-and-data-status.md`'s own definition) passes for the new partitions.
- [ ] [DATA] P2. **Cut the live sports odds writers over to the new instrument_types and un-drain** (reverse of the
      pre-drain todo above). (repo: market-data-processing-service / deployment-service). **Done when**: a fresh live
      write is observed landing under the new instrument_types and the drain flag is confirmed lifted.
- [ ] [DATA] P2. **Retire the legacy `odds` contract entry + the dual-read path once no object/manifest row remains
      under `odds`** (requires the `[OPERATOR]`-gated 3-venue move above to have landed too) **and a full corpus re-read
      confirms parity.** (repo: unified-api-contracts). **Done when**: a corpus-wide census confirms 0 remaining
      objects/manifest rows carrying the legacy `odds` instrument_type value, and the dual-read code path is deleted.
- [ ] [REVIEW] P2. **Post-phase codex audit**: update `/codex/02-data/availability-manifest-and-data-status.md` + the
      sports canonical-naming codex doc with the new instrument_types + migration order. (repo: unified-trading-pm).
      **Done when**: both named codex docs cite EXCHANGE_ODDS/FIXED_ODDS and the migration ordering used.

## Codex SSOTs

`/codex/02-data/availability-manifest-and-data-status.md`, `/codex/02-data/sports-data-types-catalog.md`,
`/codex/05-infrastructure/gcs-object-operations.md`. Plan↔codex drift is review-blocking.
