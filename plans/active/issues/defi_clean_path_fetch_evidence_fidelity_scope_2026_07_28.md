---
doc_type: issue
title: DeFi clean-path fetch evidence fidelity — true scope is 25+ call sites, not one bounded change
summary: >-
  cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md's Track H item (c) ("thread the ACTUAL subgraph/RPC HTTP
  status into the defi handlers' clean-path record_zero_rows/record_empty(SOURCE_RETURNED_ZERO) calls instead of the
  recorder's synthesized clean_fetch_evidence") turns out NOT bounded as scoped — a live-probe of the actual call sites
  found 25+ handlers across non-uniform fetch mechanisms (subgraph HTTP POST, Alchemy RPC multicall, on-chain Chainlink
  calls, Solana RPC), most of which never have the real HTTP status in local scope at the manifest-recording call site
  at all (it is read several frames deeper, purely for retry-loop/404 decisions, then discarded). One handler
  (governance_adapter.py) additionally swallows a genuine fetch error into an empty list — a correctness gap the "danger
  class already closed" framing assumed didn't exist. This doc captures the discovered scope + files it as a properly
  scoped follow-up rather than absorbing it into the single P1 dispatch todo.
status: open
nature: issue
asset_group:
  [defi] # corrected 2026-07-29 (/ag-closeout-audit defi, Phase 0.3 Orthogonality HARD CHECK) -- was
  # [defi, cross-cutting], a genuine mistag: this doc forked out of cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md
  # as a scoping correction but its content (25+ call sites, all named handlers under market-tick-data-service's DeFi
  # handler tree -- evm_defi_collectors.py, aave_oracle, solana_defi_handler.py, etc.) is 100% DeFi-specific, not a
  # generic cross-AG pattern; classic "fork inherits parent's cross-cutting tag verbatim" bug class per the skill.
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [defi, honest-coverage, fetch-evidence, fidelity, manifest]
related:
  [
    ../cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md,
    ../data_pipeline_ag_residual_backfill_decisions_2026_07_24.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-28"
last_updated: "2026-08-02"
source: sports_consolidated_native_ao_extract-010/cross_cutting_satellite_ao_dispatch_batch2-011 dispatch (slot-11)
resolved_by:
locked_by:
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope: [/codex/02-data/honest-absence-downstream-handling.md, /plans/active/task_template.md, /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md, market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py, /plans/active/defi_consolidated_closeout_2026_07_18.md, unified-api-contracts/unified_api_contracts/canonical/crosscutting/honest_coverage.py]
---

# DeFi clean-path fetch-evidence fidelity — scoping correction

## What I found

`cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`'s Track H item (c) reads: "thread the ACTUAL subgraph/RPC
HTTP status into the defi handlers' clean-path `record_zero_rows`/`record_empty(SOURCE_RETURNED_ZERO)` calls instead of
the recorder's synthesized `clean_fetch_evidence`" — framed as a P2 "Nicety" (danger class already closed, this is
fidelity not correctness) bundled into one P1 dispatch todo alongside two other, genuinely bounded, items.

A research pass over `market-tick-data-service` found:

- `clean_fetch_evidence()` (`cli/handlers/_defi_manifest.py:314-346`, a `DefiManifestRecorder` staticmethod) hardcodes
  `http_status=200` — never derived from a real response. It is the fallback `_resolve_zero_rows_reason_and_evidence`
  uses whenever `record_zero_rows(...)` omits `fetch_evidence` — so EVERY clean-path call that doesn't explicitly build
  its own evidence silently synthesizes this fake 200, not just the handlers that call it by name.
- UAC's `build_fetch_evidence()` (`unified_api_contracts/canonical/crosscutting/honest_coverage.py:507`) already accepts
  a real `http_status: int | None` and resolves `error_signal` from it via `fetch_error_signal_for_status()` — the
  correct target function. It is not currently used by any MTDS defi clean-path call site.
- **25+ call sites** hit the pattern (`record_zero_rows`/`record_empty(..., "SOURCE_RETURNED_ZERO", ...)` on the
  post-success `if not rows:` branch, `fetch_evidence` omitted or built via `clean_fetch_evidence`), spanning:
  `evm_defi_collectors.py`, `_aave_oracle_collection.py`, `oracle_prices_handler.py` (Chainlink + Pyth legs),
  `aggregator_route_handler.py`, `orca_whirlpool_state_handler.py`, `governance_proposals_handler.py`,
  `protocol_outage_detector_handler.py`, `liquidation_events_handler.py`, `jupiter_quote_handler.py`,
  `flash_loan_events_handler.py`, `_lending_grain.py` (shared by `risk_params_handler.py` + others),
  `eigenlayer_rewards_handler.py`, `token_transfers_handler.py`, `lst_rates_handler.py`,
  `raydium_classic_amm_handler.py`, `position_data_handler.py`, `_dex_pools_subgraph.py`,
  `vault_share_price_handler.py`, `solana_defi_handler.py`, `bridge_events_handler.py`, `mev_events_handler.py`,
  `staking_yields_handler.py`, `governance_events_handler.py`, `gas_fee_handler.py`, `phoenix_orderbook_handler.py`,
  `_dex_swaps_queries.py`. `perp_funding_handler.py` hand-builds the same fabricated-200 `FetchEvidence` inline (a
  variant of the same pattern, not via `clean_fetch_evidence`).
- **In every site inspected, the real HTTP status is NOT in local scope at the manifest-recording call.** It is read
  only inside a low-level fetch helper several call-frames deeper (`_run_subgraph_http`, `async_post_to_subgraph`, the
  Solana RPC helpers, etc.) purely for retry-loop/404 branching, then discarded — the helper's return type is always the
  parsed rows/JSON, never `(data, http_status)`. Threading the real status up therefore requires widening the RETURN
  SIGNATURE of each of these fetch helpers (a handler-by-handler, non-uniform refactor), not a find-and-replace at the
  manifest-recording sites.
- **Not all fetch mechanisms even have an "HTTP status"**: Aave uses an Alchemy RPC batch call (no per-call HTTP status
  surfaced to the caller at all); Chainlink/Pyth use on-chain calls; several Solana sites build a DataFrame from an
  already-completed RPC-polling helper with no response object in scope.
- **One genuine correctness gap, not just fidelity**: `governance_adapter.py::_fetch_subgraph_proposals` and
  `_fetch_snapshot_proposals` both `except (aiohttp.ClientError, OSError, ValueError): return []` — a REAL HTTP error
  (`resp.raise_for_status()` raising on 4xx/5xx is an `aiohttp.ClientError` subclass) is swallowed into an empty list,
  which the caller (`governance_proposals_handler.py::_write_or_empty`) then honestly-but-wrongly records as
  `SOURCE_RETURNED_ZERO` with fabricated evidence — exactly the C1 danger class `clean_fetch_evidence()`'s own docstring
  says is "a SEPARATE bug fixed in the collector (raise → record_failed), NOT a reason to weaken this evidence." This
  specific handler has NOT had that fix, contradicting the source todo's blanket "danger class already closed" framing.
  `fetch_governance_proposals` also merges TWO independent sources (subgraph + Snapshot) per call, so even a fixed
  version has no single scalar "the" HTTP status to report — the merge itself needs a design decision (report
  per-source? report the worse of the two? track both up through `_write_or_empty`?) before a fidelity fix can even be
  written for this handler.

## Why it matters

The source todo bundled this into a single P1, ~1-hour dispatch alongside two genuinely bounded items (the tradfi
`ohlcv_15s` tier fix — shipped `market-data-processing-service@034c1df` — and the already-resolved UAC image-packaging
bug). Item (c) as literally scoped ("the defi handlers pass real HTTP status through with a test") is a multi-file,
non-uniform, ~25-call-site refactor plus at least one design decision (the governance dual-source merge) — not a
bounded, worker-determinable-alone todo per `task_template.md`'s dispatch-scope eligibility rule. Attempting it inside
the single dispatch would have meant either a rushed, under-reviewed change across 25+ files in DeFi data-capture code
(high blast radius — data-pipeline correctness is a HARD RULE) or silently claiming "done" on a fake/partial fix.
Neither is acceptable, so this doc exists to make the true scope visible and dispatchable properly instead.

## Recommended decision

Split into two tracks, both P2 (matches the source doc's own "Nicety" framing — the DANGER class is genuinely closed for
the shared-helper-based sites; only `governance_adapter.py` needs the C1 fix at higher priority). Left `assigned_vm: NA`
at this doc's own frontmatter level (this is a scoping/triage document, not a pre-vetted dispatch-ready backlog — item 2
below is explicitly gated on a human design call) — a future triage pass should spin item 1 off into its own
`assigned_vm: planning` dispatch todo once picked up, since it alone is genuinely bounded.

- [x] ✅ [CODE] P1. **Fix the `governance_adapter.py` swallowed-exception bug** (the one real correctness gap found
      here, market-tick-data-service): raise on a genuine HTTP/network error from `_fetch_subgraph_proposals`/
      `_fetch_snapshot_proposals` (both currently `except (aiohttp.ClientError, OSError, ValueError): return []`)
      instead of returning `[]`, so the per-protocol caller's existing `record_failed` path (not the clean-empty path)
      catches it — mirrors the C1 fix pattern already applied elsewhere per `clean_fetch_evidence()`'s own docstring
      citation. This alone does NOT require threading real HTTP status through anything; it is a bounded, single-file,
      testable fix. **Done when**: a test proves a simulated 5xx/network error on either fetch path reaches
      `record_failed`, not a silent empty-list `SOURCE_RETURNED_ZERO`; existing "genuinely zero proposals this window"
      behavior is unchanged. **DONE (na-eligibility-audit 2026-08-03)** —
      `defi_satellite_ao_dispatch_batch6_2026_07_30.md`:121 shipped this exact fix: `market-tick-data-service@d74984b0`
      (+ fixup `d040d457`) removed the swallow so both fetch functions let a genuine transport error propagate to
      `record_failed` while a real empty-200 response still short-circuits to `[]`; `_fetch_both_sources` switched to
      `asyncio.gather(..., return_exceptions=True)`; new unit tests cover genuine-empty vs HTTP-error vs
      connection-error plus a `_process_protocol`-level test proving the error reaches `record_failed` not
      `record_zero_rows`.
- [ ] [DIAG] P2. **Aave/Alchemy RPC family — determine whether a per-call HTTP status is even obtainable** from the
      Alchemy RPC batch client `_aave_oracle_collection.py` uses. If not, this family cannot be closed the same way as
      the HTTP-subgraph family — report that and propose the alternative (RPC-level error code? nothing to thread?)
      rather than guessing. Read-only research, no code change. (market-tick-data-service)
- [ ] [DIAG] P2. **Chainlink/Pyth on-chain family — same "is there an HTTP-status-equivalent" question** as the Aave
      item above, for `oracle_prices_handler.py`'s Chainlink + Pyth legs. Read-only research, no code change.
      (market-tick-data-service)
- [ ] [CODE] P2. **Subgraph-HTTP family — thread real status through the direct `async_post_to_subgraph` callers**
      (verified 2 real callers today: `dex_swaps_handler.py`, `liquidations_handler.py` — RE-VERIFY this count at
      dispatch time, don't trust it stale) by widening `async_post_to_subgraph`'s return to `(payload, http_status)` and
      updating both callers. **Scoping note**: as of this doc's writing, NEITHER of those 2 callers actually calls
      `record_zero_rows`/`record_empty` on their clean-empty path (confirmed by grep) — so this todo's real value is
      establishing the pattern for OTHER subgraph-HTTP helpers (`_run_subgraph_http` in `evm_defi_collectors.py`,
      `governance_adapter.py`'s inline `session.post`, etc.), each of which needs its OWN per-file widen (not a shared
      helper) — re-scope this todo to the actual highest-value single file once picked up, don't attempt all of them in
      one dispatch. (market-tick-data-service)
- [ ] [LOCAL] P2. **`governance_proposals_handler.py`'s dual-source merge — resolve the "report which source's status"
      design question** (subgraph + Snapshot are two independent fetches per call; there is no single scalar "the" HTTP
      status once both are queried and merged) as a human/local decision FIRST (per
      `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — this is a
      judgment call, not a checkable fact), THEN file the scoped CODE todo against that decision. Options to weigh:
      report per-source (2 fields), report the worse of the two, or track both up through `_write_or_empty` and let the
      caller decide. Do not dispatch a CODE todo for this handler before the decision lands.

## Codex SSOTs

- `/codex/02-data/honest-absence-downstream-handling.md` (the 4-state capture_status contract this fidelity work sits
  inside).
- `plans/active/task_template.md` § dispatch-scope eligibility (why this doc exists instead of a rushed 25-site change).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - doc explicitly self-declares NA at its own frontmatter level and
  carries a [LOCAL] todo citing dispatch-scope eligibility as a human design call
- **context-scout 2026-08-01**: populated context_scope (5 entries).
- **na-eligibility-audit 2026-08-02** (tranche=defi, autonomous, scheduled): KEEP-NA valid (2026-07-30 verdict re-
  affirmed) — re-read end to end, 5 open items; content unchanged since that verdict (the only edit was context- scout's
  `context_scope` backfill). The doc's own "Recommended decision" section self-declares NA at the frontmatter level and
  its `[LOCAL] P2` item cites dispatch-scope eligibility for a genuine human design call (the
  `governance_proposals_handler.py` dual-source merge has no single scalar HTTP status to report). Its `[CODE] P1`
  governance_adapter fix is genuinely bounded and the doc says so — but it is one item inside a doc whose other 4
  include that undecided design call and a `[CODE] P2` the doc itself says to "re-scope to the actual highest-value
  single file once picked up", so a whole-doc flip would dispatch under-scoped work. Left for a future extraction rather
  than reclassified.
- **context-scout 2026-08-03**: populated/refreshed context_scope (6 entries).
