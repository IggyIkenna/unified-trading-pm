---
doc_type: issue
title:
  Betfair `/`-delimited instrument_id is a cross-repo convention (3 repos), not a lone instruments-service bug — fixing
  it needs coordination, not a single-repo edit
summary: |
  The 2026-07-08 canonical-instrument-id audit flagged instruments-service's Betfair reference-data adapter
  (`instrument_key = f"{market_id}/{selection_id}"`) as "the most degenerate raw-passthrough found" versus the
  workspace's `VENUE:TYPE:SYMBOL` convention. Deeper investigation found the SAME `market_id/selection_id` `/`-shape
  independently built and PARSED in strategy-service (position adapter + a real `rsplit("/", 1)` fill-event parser)
  and execution-service (order placement + order listing), plus a THIRD, differently-shaped MTDS format
  (`VENUE_KEY:SPORT:market_id`, market-level only) for live streaming. Changing only instruments-service's delimiter
  to `:` would not fix any currently-manifesting bug (Betfair reference-data fetching is not wired into the
  production sports pipeline today — confirmed 0 Betfair rows in the real `prod/catalog.parquet`), but WOULD create a
  new 3-way format inconsistency with two sibling repos this session could not touch, risking a real future breakage
  of strategy-service's fill-event instrument_id parser. Left unfixed pending a coordinated, cross-repo decision.
status:
  resolved # was: open — corrected 2026-07-14, doc-reconciliation finding 195: CLOSED BY-DESIGN 2026-07-12
  # (operator ruling, plan-reconciliation finding 341) per `active/canonical_id_builder_retrofit_checklist_2026_07_08.md`'s
  # P2 item, never synced back to this doc
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service, strategy-service, execution-service, market-tick-data-service]
scope: [engineer]
tags:
  [
    betfair,
    instrument-id,
    canonical-id,
    cross-repo,
    sports,
    execution,
    position-tracking,
    delimiter-convention,
    audit-followup,
  ]
related:
  [
    instruments-service/docs/SPORTS_INSTRUMENTS.md,
    plans/audit/results/canonical_instrument_id_audit_2026_07_08.md,
    plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md,
  ]
created: 2026-07-08
last_updated: 2026-07-14
parent_epic: sports_master
priority: P2
source:
  SUB_AGENT_MANDATORY_RULES dispatch (slot-3 this session) — "Betfair's real / delimiter bug" fix task, instructed to
  check real downstream consumers before shipping
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
  operator ruling 2026-07-12 (plan-reconciliation finding 341, docs-only — Option 1 below, "Formalize `/` as Betfair's
  own per-provider convention" — see `active/canonical_id_builder_retrofit_checklist_2026_07_08.md`'s P2 item for the
  CLOSED BY-DESIGN record)
audited_scope: cross-repo-consistency
---

# Betfair instrument_id `/` delimiter is a cross-repo convention, not an isolated bug

## What I was asked to do

Fix `instruments-service/instruments_service/reference_data/adapters/sports/adapters/betfair.py:279`
(`_build_runner_record`), which builds `instrument_key = f"{market_id}/{selection_id}"` — a raw `/`-joined pair,
diverging from the workspace's `VENUE:TYPE:SYMBOL` `:`-delimited convention used by every CeFi/DeFi/TradFi/Prediction
adapter (confirmed by grepping ~60 `instrument_key=f"..."` call sites across
`instruments_service/reference_data/adapters/` — all but Betfair and Polymarket, which uses a bare on-chain hash, use
`VENUE:TYPE:SYMBOL`). The instruction was explicit: confirm the fix is corrective, not breaking, by checking for real
downstream consumers before shipping — same diligence as the weather stale-GCS-path fix shipped earlier this session
(`instruments-service@2b45cb78`).

## What I found

**The audit that flagged this (`plans/audit/results/canonical_instrument_id_audit_2026_07_08.md:165`, "Betfair stores
raw `marketId/selectionId` with `/` instead of `:` — the most degenerate raw-passthrough found") only looked at
instruments-service.** It did not check whether any other repo depends on the current format. It does.

Grepping the workspace for `market_id.*selection_id` / `instrument_id.split` patterns surfaced THREE independent, real
(non-test) implementations of the exact same `{market_id}/{selection_id}` shape, all using `/`:

1. **instruments-service** (this task's target) — `betfair.py:279`, `_build_runner_record`:
   `instrument_key = f"{market_id}/{selection_id}"`. Reference-data adapter, `venue="betfair"`,
   `instrument_type=EXCHANGE_ODDS`.
2. **strategy-service** — `strategy_service/position/position_interface/adapters/betfair.py:15,42,76`
   (`BetfairPositionAdapter._map_order_to_position`, docstring: "Position mapping convention: instrument_id =
   `{market_id}/{selection_id}`"), built independently from Betfair's `listCurrentOrders` API response fields, NOT from
   instruments-service's `InstrumentRecord`.
3. **strategy-service** — `strategy_service/position/core/fill_event_consumer.py:59-75` (`_convert_to_sports_fill`): a
   REAL, ACTIVE PARSER —
   `if "/" in inst: fixture_id, selection = inst.rsplit("/", 1) else: fixture_id = inst; selection = "unknown"`. This is
   the consumer that would silently mis-parse if fed a colon-delimited id: no `/` present → falls into the `else` branch
   → `fixture_id` becomes the WHOLE glued string and `selection` is lost (defaults to the literal string `"unknown"`).
   This is a genuine regression risk, not a hypothetical one — the parsing branch already exists and already
   special-cases "no `/` found."
4. **execution-service** — `execution_service/sports_execution/adapters/exchanges/betfair_order_mapping.py:120,180,286`
   (`place_order` / `_parse_place_response` / `_order_to_canonical`): builds
   `instrument_id=f"{market_id}/{selection_id}"` for both order-placement and order-listing paths, independently from
   the Betfair order API responses.
5. **market-tick-data-service** — `market_tick_data_service/live/connectors/betfair_ws.py:37-39,75-91` documents and
   parses a FOURTH, differently-shaped format for live streaming subscriptions: `"{VENUE_KEY}:SPORT:{market_id}"`
   (market-level only, no selection_id; `_parse_market_id` does `instrument_id.split(":", maxsplit=2)`). This connector
   is a BLOCKED-CREDENTIALS scaffold (no live traffic yet), so it is not itself at risk, but it shows a THIRD id-shape
   already exists for the same underlying Betfair market.

**Production-impact check (real GCS read, not just static code reading):** downloaded and read the real
`gs://instruments-store-sports-prd-central-element-323112/prod/catalog.parquet` (116 rows). Zero rows have
`venue="betfair"` or a `/`-containing `instrument_id` — Betfair reference-data fetching is not currently wired into the
production SPORTS asset-group pipeline at all (`instruments_service/engine/orchestrator/venue_core.py:349-368`,
`get_venues_for_asset_groups()`, explicitly excludes `BETFAIR*` from the SPORTS venue list — "Decision C (operator
2026-06-29): two separate registries; this list is IS-owned and EXEMPT from the set-equality invariant with UAC" —
Betfair is documented as MTDS-owned for market/odds data, not IS-fetched). So the instruments-service Betfair adapter's
`get_instruments()` is reachable only via the general `reference_data/factory.py`/`router.py` (e.g. an ad-hoc
`--venue betfair` CLI call), not the automated sports batch pipeline, and has zero callers anywhere else in the repo
outside its own tests.

## Why I did not make the naive single-repo fix

Changing `instrument_key = f"{market_id}/{selection_id}"` to use `:` in instruments-service ALONE would:

- **Not fix any currently-manifesting bug** — the code path producing this string is dormant in production (0 rows
  today), so there is no live catalog data to correct.
- **Create a NEW, real inconsistency**: three sibling implementations (strategy-service ×2, execution-service) would
  continue emitting/parsing `/`, while instruments-service alone would emit `:` for what is conceptually the SAME
  Betfair market+selection identity. The workspace's Batch=Live determinism architecture
  (`codex/09-strategy/operational/paper-batch-live-reconciliation.md`) explicitly requires a canonical `InstrumentKey`
  that different services can join on by string equality — a delimiter mismatch between the reference-data plane and the
  execution/position plane for the same instrument breaks that join the moment anything (features-service,
  strategy-service reference lookups) tries to correlate a Betfair fill/position with instruments-service's Betfair
  reference row.
- **Was outside this session's edit scope regardless** — this slot's dispatch explicitly restricted edits to
  `instruments-service` only; strategy-service and execution-service belonged to sibling agents this round, so even a
  "fix all four" approach was not executable in this session.

Given the task's own standard ("confirm your fix is corrective, not breaking"), and that I could not make the fix
corrective without touching two out-of-scope repos, I left the code as-is and am filing this issue instead of shipping a
change I could not verify was safe.

## Recommended decision — **DECIDED, CLOSED BY-DESIGN 2026-07-12** (was: "needs an operator/cross-repo call, not a

unilateral code change" / open 2-option question — corrected 2026-07-14, doc-reconciliation finding 195: the operator
ruled 2026-07-12 (plan-reconciliation finding 341, recorded in
`active/canonical_id_builder_retrofit_checklist_2026_07_08.md`'s P2 item) in favor of **Option 1 below**: `/` is
Betfair's documented native id convention; canonical ids for Betfair KEEP the `/` delimiter and downstream consumers
must treat it as venue-native, not normalise. Option 2 ("Coordinated migration to `:`") was NOT chosen. This doc's
frontmatter/body had never been synced back to reflect that ruling until this pass.)

Two real options were on the table, either legitimate — kept below for the record of what was actually decided between:

1. **Formalize `/` as Betfair's own per-provider convention** (cheap, docs-only): analogous to the operator's existing
   sports-wide decision that `LEAGUE:MATCHUP:DATE` is a legitimate alternative to `VENUE:TYPE:SYMBOL`
   (`instrument_id_format_canonicalization_2026_07_08.md`), formally bless `market_id/selection_id` as Betfair's
   native-shape convention (Betfair's own API addresses instruments this way) across all three real implementations, and
   correct the audit's "degenerate raw-passthrough" framing in
   `plans/audit/results/canonical_instrument_id_audit_2026_07_08.md`.
2. **Coordinated migration to `:`** (more expensive): a single cross-repo change touching
   `instruments-service/instruments_service/reference_data/adapters/sports/adapters/betfair.py`,
   `strategy-service/strategy_service/position/position_interface/adapters/betfair.py`,
   `strategy-service/strategy_service/position/core/fill_event_consumer.py` (update the `/`-split parser to also accept
   `:`), and `execution-service/execution_service/sports_execution/adapters/exchanges/betfair_order_mapping.py` — plus
   deciding whether MTDS's separate `VENUE_KEY:SPORT:market_id` live-stream format should also be reconciled (it
   currently omits `selection_id` entirely, so it is not a strict superset/subset of either shape).

No code changed in this session for this finding. `instruments-service/docs/SPORTS_INSTRUMENTS.md`'s "Known gaps"
section has been updated to cite this issue doc instead of describing the delimiter swap as a pending mechanical fix.
