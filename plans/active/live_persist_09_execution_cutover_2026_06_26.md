---
title:
  Live-persist 09 — execution-service cutover to the facade (STREAM_ONLY fills/positions/PnL; reconcile with the global
  ledger)
created: 2026-06-26
parent_epic: batch_live_symmetry_master
assigned_vm: human-planning
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2

priority: P2
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Live-persist 09 — execution-service cutover

Child #9 (PARALLEL with 06/07/08 once 01–05 land). **Single repo: execution-service.** Parent:
`live_data_persistence_central_event_log_2026_06_25.md`. Worker context = execution-service only.

> Read `SUB_AGENT_MANDATORY_RULES.md`. Ship via `quickmerge --agent --files`; QG-green before commit. UAC types only; no
> service↔service imports. Client-funds-isolation HARD RULE unaffected (single `client_id` per intent).

## Shared contract (recap)

Execution fills/positions/PnL + the paper ledger are **STREAM_ONLY / IRREPRODUCIBLE** (no external backfill — they ARE
the system of record) → cold GCS + BQ-view FOREVER, no TTL. **The UAC global ledger (`canonical.crosscutting.ledger`)
stays the writer-of-record** — this cutover makes execution **declare `stream_only` through the SINK_MATRIX +
publish/read via the facade**, NOT re-persist what the ledger already holds (confirmed by plan 00's ledger-coverage
audit).

## Anchors (start here — grep, sub-agent if large)

The 4 ledgers (Instruction/Position/Passive/Pricing) write path; the live market-data/mark consume into the matching
engine; `PaperMatchingEngine`; `StreamConsumerGroup`/`build_event_sink`/`messaging_protocol` usages.

## Todos

- [x] [EXECUTION] P1. Consume live market-data/marks via the UTL facade (canonical envelope); colocated engine =
      in-memory transport, live = Pub/Sub. — execution-service@7fc9c5fd — InMemoryTransport round-trip test passes;
      facade_read/publish wired; finding: no pre-existing direct Redis/PubSub mark-consume code (execution-service did
      not previously consume live candles directly — the facade layer is now the declared consume path).
- [x] [EXECUTION] P1. Declare execution output shards `STREAM_ONLY` in the matrix; ensure their durable home is the
      global ledger (no double-write) and that ledger rows are reachable for batch-replay via the facade `read()`. —
      execution-service@7fc9c5fd — SINK_MATRIX already has all four execution shards (execution_fills,
      execution_positions, execution_pnl, paper_ledger) as STREAM_ONLY/cold_ttl_days=None (wildcard "\*" entry). UAC
      global ledger remains writer-of-record. Contract test asserts this.
- [x] [EXECUTION] P0. Contract test: STREAM_ONLY shards get the forever cold lifecycle (no TTL); ledger remains
      writer-of-record; intra-client single-`client_id` invariant intact; QG-green. — execution-service@7fc9c5fd —
      tests/unit/test_facade_cutover_contracts.py: 3 tests pass, QG green (209s).

## Success criteria

execution `quality-gates.sh` exits 0; live market-data consume via the facade; execution state declared STREAM_ONLY +
durable on the ledger (no re-persist); shipped via quickmerge.

## Dependencies / unblocks

Deps: 01, 02, 05 (marks/candles). Unblocks: 10 (determinism verify — uses execution fills for paper(W)).
