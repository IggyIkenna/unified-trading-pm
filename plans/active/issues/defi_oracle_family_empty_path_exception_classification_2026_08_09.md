---
doc_type: issue
title:
  DeFi RPC-oracle families (Aave, Chainlink) aggregate-zero-path exception ambiguity + Pyth 404 fidelity — deferred
  design questions from defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md's DIAG findings
summary: >-
  defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md's Aave/Alchemy and Chainlink/Pyth DIAG todos (checkboxes
  2-3, both closed) each surfaced a genuine follow-up in PROSE only — never converted to a tracked `- [ ]` todo, which
  the archival-discipline codex doc (§2, "every follow-up is a canonical todo, never prose") flags as its own defect
  class. Filed here per that doc's step-1 archival-ritual requirement (migrate any deferred item into a real tracked
  todo before archiving the source doc). Three items: (1) Aave's per-reserve RPC-call swallow can hide a real error
  behind a fabricated clean empty-path — a design question (which signal to surface), same shape as the source doc's
  already-resolved item 5. (2) Chainlink's per-feed swallow has the identical ambiguity. (3) Pyth's clean-empty path
  discards an already-in-hand HTTP status, including one case where a real 404 (no data at that timestamp) is
  misreported as a synthesized 200 — this one is bounded/CODE-eligible, not a design question.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, honest-coverage, fetch-evidence, fidelity, manifest, rpc, oracle]
related:
  [
    /plans/archive/2026_08/issues/defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: "2026-08-09"
author: slot-6
last_updated: "2026-08-09"
source:
  defi_clean_path_fetch_evidence_fidelity_scope-003 dispatch (slot-6), migrated during that doc's archival per
  /codex/12-agent-workflow/plan-completion-and-archival-discipline.md step 1
resolved_by:
locked_by:
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_aave_oracle_collection.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/oracle_prices_handler.py,
  ]
---

# DeFi RPC-oracle families — deferred aggregate-zero-path + Pyth fidelity follow-ups

## What I found

`defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md`'s Aave/Alchemy DIAG (checkbox 2) and Chainlink/Pyth DIAG
(checkbox 3) are both closed (read-only research, done as scoped), but each closed-checkbox's own text describes a
concrete follow-up that was never converted into a real `- [ ]` todo — a prose deferral, exactly the anti-pattern
`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` §2 names.

1. **Aave** (`_aave_oracle_collection.py`'s `query_aave_reserves`/`collect_aave_rows`): a per-reserve `except Exception`
   swallows and logs any single RPC failure without surfacing it. If every reserve call for a given day fails this way,
   the shard still reaches `record_aave_empty`'s clean path with a fabricated 200 — indistinguishable from "genuinely
   queried, all returned zero." Proposed alternative (from the source doc): classify+thread the caught exception type
   (transport `HTTPError` w/ real status vs JSON-RPC `Web3RPCError`/`ContractLogicError` vs connection/timeout) into
   `fetch_evidence`, OR surface per-reserve exception counts up so the empty-path recorder can distinguish the two
   cases. This is a genuine human design call (which signal, and how to plumb it through 6 independent per-reserve RPC
   calls) — same shape as the source doc's already-resolved item 5 (governance dual-source merge).
2. **Chainlink** (`oracle_prices_handler.py::_query_chain_feeds`): identical shape — a per-feed `except Exception`
   swallow means an all-feeds-errored chain still reaches `_record_chainlink_empty`'s clean path with a fake 200. Same
   design question as Aave (classify+thread exception type, or surface per-feed exception counts).
3. **Pyth** (`oracle_prices_handler.py::_fetch_pyth_prices`/`_fetch_pyth_prices_at_timestamp`): DIFFERENT — the real
   HTTP status IS already in local scope at the fetch call site (`_hermes_latest_get` returns `resp.status` directly)
   but is discarded on the clean-empty `record_zero_rows` path, which falls through to the generic synthesized 200.
   Concrete correctness wrinkle: `_fetch_pyth_prices_at_timestamp` returns `[]` (not an error) on a genuine Hermes 404
   ("no data at this timestamp") — that flows to the same clean-empty path, so the synthesized `http_status=200` is
   provably wrong in that specific case (real status was 404). This one is bounded/CODE-eligible, not a design question
   — purely a threading exercise (widen the two functions' return signature to also carry the resolved `http_status`,
   thread it into `build_fetch_evidence(http_status=..., source="pyth_hermes")` at the `_emit_pyth_manifest` call site),
   no new exception-narrowing needed.

## Why it matters

Items 1-2 are a real (if minor) honest-absence fidelity gap: an all-calls-errored aggregate shard is currently
indistinguishable from a genuinely-empty one in the manifest. Item 3 is a provable factual inaccuracy in already-fetched
data (a real 404 recorded as a fake 200), not just an imprecision — same class of gap the source doc's
`governance_adapter.py` correctness fix (item 1) closed for the subgraph family. None are urgent (all three are dormant
unless the underlying family goes fully dark for a day, or a Hermes-404 no-data window occurs), which is why this stays
P3.

## Recommended decision

- [ ] [LOCAL] P3. **Resolve the Aave/Chainlink aggregate-zero-path signal design question** (which of: classify+thread
      the caught exception type into `fetch_evidence`, vs surface per-reserve/per-feed exception counts up to the
      empty-path recorder) as a human/local decision FIRST — mirrors
      `defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md`'s already-resolved item 5 pattern. THEN file the
      scoped CODE todo(s) against that decision (market-tick-data-service: `_aave_oracle_collection.py` +
      `oracle_prices_handler.py`'s Chainlink leg).
- [ ] [CODE] P2. **Thread Pyth's already-in-hand HTTP status into the clean-empty path** (market-tick-data-service):
      widen `_fetch_pyth_prices`/`_fetch_pyth_prices_at_timestamp`'s return signature to also carry the resolved
      `http_status` (200 on the normal empty-after-filter path, 404 on the Hermes no-data-at-timestamp case), and thread
      it into `_emit_pyth_manifest`'s `record_zero_rows` call via
      `build_fetch_evidence(http_status=..., source="pyth_hermes")` instead of falling through to the generic
      synthesized 200. **Done when**: a test proves a simulated Hermes 404 (no data at timestamp) records
      `http_status == 404` on the clean-empty path, and a genuine empty-after-filter 200 response still records
      `http_status == 200`; existing behavior otherwise unchanged.

## Codex SSOTs

- `/codex/02-data/honest-absence-downstream-handling.md` (the 4-state `capture_status` contract this fidelity work sits
  inside).
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (why this doc exists — migrating a prose
  deferral into a real todo per the archival ritual's step 1).

## Progress Log

- **defi_clean_path_fetch_evidence_fidelity_scope-003 dispatch (slot-6, 2026-08-09)**: filed while archiving
  `defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md` (all 6 of its own todos done, unlocked —
  archival-eligible per the codex ritual). That doc's checkboxes 2-3 each described a genuine follow-up only in prose;
  migrated both here as real todos before the archival landed.
- **context-scout 2026-08-09**: re-scouted; fixed a wrong path (`_aave_oracle_collection.py` actually lives under
  `cli/handlers/`, not `market_interface/adapters/defi/`), swapped `/plans/active/task_template.md` for
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (cited in the doc's own "Codex SSOTs" section
  but missing from context_scope), context_scope now 4 entries.
