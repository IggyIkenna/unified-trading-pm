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
author: unknown
last_updated: "2026-08-02"
source: sports_consolidated_native_ao_extract-010/cross_cutting_satellite_ao_dispatch_batch2-011 dispatch (slot-11)
resolved_by:
locked_by:
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/02-data/honest-absence-downstream-handling.md,
    /plans/active/task_template.md,
    /plans/archive/2026_07/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/honest_coverage.py,
  ]
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
the shared-helper-based sites; only `governance_adapter.py` needs the C1 fix at higher priority). **Frontmatter flipped
`assigned_vm: NA` → `planning` 2026-08-08**: the last remaining human-design-call item (the governance dual-source merge
question, formerly item 5) is now resolved and reclassified below — that was the sole documented blocker per this doc's
own 2026-08-08 Progress Log entry ("Item 5 ... remains the genuine unresolved human decision keeping the whole doc
`assigned_vm: NA`"); items 2-3 (Aave/Alchemy + Chainlink/Pyth research) stay open here but are `KEEP-NA-STALE`
duplicates already covered by `defi_satellite_ao_dispatch_batch9_2026_08_06.md:175-179` (status: active) — non-blocking,
close by citation once batch9 ships.

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
- [x] ✅ [DIAG] P2. **Aave/Alchemy RPC family — determine whether a per-call HTTP status is even obtainable** from the
      Alchemy RPC batch client `_aave_oracle_collection.py` uses. If not, this family cannot be closed the same way as
      the HTTP-subgraph family — report that and propose the alternative (RPC-level error code? nothing to thread?)
      rather than guessing. Read-only research, no code change. (market-tick-data-service) **RESEARCHED (2026-08-08)** —
      **not obtainable on the success path; only partially obtainable on failure; no single scalar applies anyway.**
      `collect_aave_rows`/`query_aave_reserves` (`_aave_oracle_collection.py:40-113`) call
      `oracle.functions.getAssetPrice(...).call(block_identifier=...)` — web3.py's high-level contract-call API. Traced
      the transport: `Web3.HTTPProvider.make_request()` (`web3/providers/rpc.py`) calls
      `web3._utils.request.make_post_request()`, which does `response.raise_for_status(); return response.content` — the
      `requests.Response` object (and its `.status_code`) is **discarded** on the success path; `.call()`'s return value
      is only the ABI-decoded result, never the HTTP status. So on a clean 200, there is nothing to thread — the status
      is implicit and never surfaces past `make_post_request`. On a genuine transport failure, `raise_for_status()`
      raises `requests.exceptions.HTTPError`, whose `.response.status_code` DOES carry the real non-2xx code —
      technically obtainable, but only by narrowing the current broad `except Exception` (in both
      `query_aave_reserves`'s per-reserve loop and `collect_aave_rows`'s setup try/except) to specifically catch
      `requests.exceptions.HTTPError` and read that attribute; every other web3 failure mode (JSON-RPC-level error on an
      HTTP-200 response, e.g. a reverted call → `Web3RPCError`/`ContractLogicError`; connection/timeout errors) has no
      HTTP status at all, by definition. Separately — even if threaded — **there is no single "the" HTTP status for this
      shard**: `query_aave_reserves` calls `getAssetPrice` once **per reserve** (6 reserves in `_AAVE_ORACLE_ASSETS`,
      `_oracle_prices_constants.py:334-341`), each its own independent RPC call/HTTP POST, plus
      `get_block_by_timestamp`'s binary search issues its own multiple `eth_getBlockByNumber` calls — same structural "N
      independent calls, no single scalar" shape as the already-resolved governance dual-source case (item 5 above),
      just wider (up to 6+ calls, not 2). **Proposed alternative signal**: since HTTP status isn't the natural unit for
      an RPC-batch family, the more meaningful signal already exists as the caught exception itself — classify it
      (transport `HTTPError` w/ real status code vs JSON-RPC `Web3RPCError`/`ContractLogicError` vs connection/timeout)
      and thread THAT classification (not a literal int) into `fetch_evidence`, OR — more honestly — surface per-reserve
      exception counts up from `query_aave_reserves` so `record_aave_empty`'s aggregate-zero path can distinguish
      "genuinely queried, all returned 0" from "one or more RPC calls errored and were silently continued past" (the
      per-reserve `except Exception` currently swallows and logs only). That distinction is a real design question
      (mirrors item 5's shape) — out of scope for this read-only DIAG todo; filing it here as the concrete next step
      rather than attempting it inline. **Chainlink/Pyth (the other half of this doc's original combined scope) NOT
      researched by this pass** — `defi_satellite_ao_dispatch_batch9_2026_08_06.md:175-179`'s combined todo still needs
      that half before it can ship; this checkbox closes only the Aave/Alchemy portion.
- [ ] [DIAG] P2. **Chainlink/Pyth on-chain family — same "is there an HTTP-status-equivalent" question** as the Aave
      item above, for `oracle_prices_handler.py`'s Chainlink + Pyth legs. Read-only research, no code change.
      (market-tick-data-service) **Same extraction/citation as the Aave item above —
      `defi_satellite_ao_dispatch_batch9_2026_08_06.md:175-179`, status: active.**
- [x] ✅ [CODE] P2. **Subgraph-HTTP family — thread real status through the direct `async_post_to_subgraph` callers**
      (verified 2 real callers today: `dex_swaps_handler.py`, `liquidations_handler.py` — RE-VERIFY this count at
      dispatch time, don't trust it stale) by widening `async_post_to_subgraph`'s return to `(payload, http_status)` and
      updating both callers. **Scoping note**: as of this doc's writing, NEITHER of those 2 callers actually calls
      `record_zero_rows`/`record_empty` on their clean-empty path (confirmed by grep) — so this todo's real value is
      establishing the pattern for OTHER subgraph-HTTP helpers (`_run_subgraph_http` in `evm_defi_collectors.py`,
      `governance_adapter.py`'s inline `session.post`, etc.), each of which needs its OWN per-file widen (not a shared
      helper) — re-scope this todo to the actual highest-value single file once picked up, don't attempt all of them in
      one dispatch. (market-tick-data-service) — market-tick-data-service@17aed396 · QG green · 2026-08-07
- [x] ✅ [LOCAL] P2. **`governance_proposals_handler.py`'s dual-source merge — resolve the "report which source's
      status" design question** (subgraph + Snapshot are two independent fetches per call; there is no single scalar
      "the" HTTP status once both are queried and merged) as a human/local decision FIRST (per
      `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — this is a
      judgment call, not a checkable fact), THEN file the scoped CODE todo against that decision. Options to weigh:
      report per-source (2 fields), report the worse of the two, or track both up through `_write_or_empty` and let the
      caller decide. Do not dispatch a CODE todo for this handler before the decision lands. **RESOLVED (2026-08-08)** —
      decision: **"worse of the two."** Read `governance_adapter.py` + `governance_proposals_handler.py` directly
      (market-tick-data-service) to confirm: `_fetch_both_sources` (`governance_adapter.py:399-416`) runs
      `_fetch_subgraph_proposals`/`_fetch_snapshot_proposals` via `asyncio.gather(..., return_exceptions=True)` then
      explicitly re-raises either exception; both fetch functions call `resp.raise_for_status()` before parsing, so any
      genuine 4xx/5xx/network error propagates all the way up. `_process_protocol`
      (`governance_proposals_handler.py:155-179`) catches that raise and routes it to `record_failed` —
      `_write_or_empty` (the clean path calling `record_zero_rows`) is only ever reached when
      `fetch_governance_proposals` returned normally, which per `_fetch_both_sources`'s re-raise means BOTH sources
      already succeeded with a genuine 2xx. So "worse of the two" is invariant-backed to always collapse to the trivial
      constant `http_status=200`, `source="subgraph+snapshot"` on this code path — zero schema change needed to UAC's
      `FetchEvidence` (`build_fetch_evidence()` already accepts `http_status: int | None`).
- [ ] [SCRIPT] P2. **Thread the resolved constant through `governance_proposals_handler.py`'s clean-path
      `record_zero_rows` call** (`_write_or_empty`, market-tick-data-service): build a `FetchEvidence` via UAC's
      `build_fetch_evidence(http_status=200, ...)`
      (`unified_api_contracts/canonical/crosscutting/honest_coverage.py:507`) with `source="subgraph+snapshot"` and pass
      it explicitly as `record_zero_rows(..., fetch_evidence=...)`, instead of falling through to
      `DefiManifestRecorder.clean_fetch_evidence()`'s generic synthesized 200. Purely for
      clarity/future-proofing/explicit provenance — the resulting recorded value is unchanged (still 200) since the
      invariant above proves it can never be anything else on this path today; if `_fetch_both_sources` is ever changed
      to tolerate a partial failure (e.g. one source optional), this call site is where a real non-200 would need to
      start flowing through. **Done when**: a test asserts the recorded `FetchEvidence.source == "subgraph+snapshot"`
      and `http_status == 200` on the governance clean-empty path; existing behavior/tests otherwise unchanged.

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
- **context-scout 2026-08-03**: re-verified context_scope (6 entries) — still accurate against the 4 remaining open
  items (Aave/Alchemy + Chainlink/Pyth research, subgraph-HTTP status threading, the governance dual-source design
  question).
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — item 5 (governance dual-source merge) remains an
  unresolved human design decision blocking whole-doc reclassify; items 2-3 partially duplicated in active batch9 (not
  yet actioned there either).
- **na-eligibility-audit 2026-08-08** (tranche=defi): KEEP-NA valid — re-read end to end. Independently re-verified the
  2026-08-07 note's "partially duplicated" framing: items 2-3 are actually a FULL verbatim duplicate (both research
  questions, merged into one combined todo, explicit `Source:` citation) in
  `defi_satellite_ao_dispatch_batch9_2026_08_06.md:175-179`, `status: active` — this is KEEP-NA-STALE (already-
  duplicated) for those two items specifically; citations added inline on both checkboxes above. Item 5 (governance
  dual-source merge design question) remains the genuine unresolved human decision keeping the whole doc
  `assigned_vm: NA` — it has no active-batch coverage and still needs the (report-per-source / worse-of-two /
  track-both) call made before any CODE todo can be filed against it. Doc stays `assigned_vm: NA`.
- **na-corpus-digest-closeout 2026-08-08**: resolved the governance dual-source design question (decision: "worse of the
  two") by reading `governance_adapter.py` (`_fetch_both_sources` re-raises either source's exception before
  `fetch_governance_proposals` returns) and `governance_proposals_handler.py` (`_process_protocol` routes any such raise
  to `record_failed`, never reaching `_write_or_empty`'s clean path) directly — proves the clean path only ever sees
  both sources already 2xx, so the decision collapses to a trivial invariant-backed constant (`http_status=200`,
  `source="subgraph+snapshot"`), zero UAC schema change needed. Reclassified the former `[LOCAL]` item as resolved +
  filed a new `[SCRIPT] P2` implementation todo to thread the constant through explicitly. This was the doc's sole
  remaining `assigned_vm: NA` blocker (items 2-3 are non-blocking `KEEP-NA-STALE` duplicates already covered by active
  `defi_satellite_ao_dispatch_batch9_2026_08_06.md`) — flipped `assigned_vm: NA` → `planning`,
  `execution_scope: local-only` → `orchestrator-agent`.
- **defi_clean_path_fetch_evidence_fidelity_scope-001 dispatch (slot-29, 2026-08-08)**: completed the Aave/Alchemy DIAG
  item (checkbox 2) — traced web3.py's `HTTPProvider.make_request()` → `make_post_request()`
  (`.venv/site-packages/web3/providers/rpc.py` + `web3/_utils/request.py`): the `requests.Response`/`.status_code` is
  discarded on the success path (`.call()` returns only the decoded ABI value), so a per-call HTTP status is not
  obtainable on success at all, only partially obtainable on failure (via
  `requests.exceptions.HTTPError.response. status_code`, requires narrowing the current broad `except Exception`), and
  no single scalar applies regardless since `query_aave_reserves` issues one independent RPC call per reserve (6
  reserves) plus `get_block_by_timestamp`'s own multi-call binary search. Proposed alternative: classify+thread the
  caught exception type, or surface per-reserve exception counts for `record_aave_empty`'s aggregate-zero path (a design
  question, filed as the concrete next step, not attempted inline — read-only DIAG scope). Chainlink/Pyth (the doc's
  other extracted half) NOT researched by this pass — `defi_satellite_ao_dispatch_batch9_2026_08_06.md:175-179`'s
  combined todo still needs that half.
