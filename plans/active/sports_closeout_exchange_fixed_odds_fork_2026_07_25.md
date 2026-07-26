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

> **Status: draft.** Per CLAUDE.md's plan-destination rule, flip to `active` only after operator review.
> **`sequential: true`** — the 11 todos below are a REAL ordering chain (mapping confirmed → drain → contracts-first →
> dual-read → GCS move → dependency_checker update → manifest reconcile → cutover → retire legacy → codex audit); this
> now machine-enforces the ordering the source block previously stated only as prose (`sports_consolidated_closeout`'s
> own "Ordering caveat" bullet, which explicitly said the prose was NOT a dispatch gate). **Caveat inherited from
> `task_template.md` §4**: todo 1 is `[OPERATOR]`-tagged and therefore non-dispatchable — it does NOT count as "the
> predecessor" in the sequential chain, so todo 2 (pre-drain) dispatches as soon as this plan is active, without waiting
> on todo 1. That is intentional: pre-drain / contracts-first / dual-read do not need the 3-ambiguous-venue mapping
> resolved (the source block's own words: "non-ambiguous poles may proceed to design without waiting"). Todo 6 is
> likewise `[OPERATOR]`-tagged and non-dispatchable, so todo 7 proceeds once todo 5 lands, without waiting on todo 6.

## Todos

- [ ] [OPERATOR] P0. **Confirm the ambiguous EXCHANGE_ODDS/FIXED_ODDS venue→class mapping for the 3 still-unresolved
      venues: bare `BETFAIR` (33 rows), `ODDS_API` (33 rows, an aggregator fitting neither class), and `PINNACLE`
      (32,616 rows — sportsbook by mechanism, but UAC models it `PINNACLE_AS_LINE` in `_SNAPSHOT_VENUES`, so confirm
      FIXED_ODDS vs a PINNACLE_AS_LINE special case).** The non-ambiguous poles are already resolved and do not wait on
      this: EXCHANGE_ODDS = `BETFAIR_EX_UK`/`BETFAIR_EX_EU`/`SMARKETS`/`MATCHBOOK`; FIXED_ODDS =
      `BETFAIR_SB_UK`/`BETMGM`. (repo: unified-trading-pm, decision record). **Done when**: this todo's own text records
      the operator's ruling for all 3 venues (a class or an explicit special case per venue).
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
- [ ] [OPERATOR] P1. **Once the mapping todo above resolves bare `BETFAIR`/`ODDS_API`/`PINNACLE`, move those venues' GCS
      objects the same way** (same snapshot → move → independent re-read count pattern as the todo above).
      `[OPERATOR]`-gated because it cannot execute correctly until the mapping decision lands — tagging it (rather than
      leaving it to silently assume the mapping todo holds it, the sequencing gap this split closes) makes the real wait
      explicit and non-dispatchable rather than implicit. (repo: market-data-processing-service / instruments-service).
      **Done when**: the same re-read-count check passes for all 3 previously-ambiguous venues once moved, citing the
      operator's ruling from the mapping todo.
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
