---
doc_type: plan
title: DeFi expected_unattempted seeder — design (capability-reconciliation RULED 2026-07-28, AO-dispatchable)
summary: >-
  Design track for the real DeFi expected_unattempted seeder ruled for on BLK-7c950d06 (Option A) — DeFi currently has
  NO expected_unattempted signal at all (MTDS orchestrator excludes every defi venue from the sentinel fan-out;
  DefiManifestRecorder has no record_expected_unattempted method), so a venue with a real UAC capability declaration is
  manifest-indistinguishable from one nobody ever declared. Per BLK-3221d4b3, this plan's first gating step —
  reconciling capability-declared-but-not-actually-collectible venues (the FLUID case) across 3 independently-drifting
  per-handler protocol lists — was an open-ended per-venue judgment call, not a worker-determinable fact. **RULED
  2026-07-28**: wire the existing FLUID-ETHEREUM adapter into the collection loop (disposition (a) — see Background).
  With that reconciliation resolved, the plan is converted to assigned_vm: planning (AO-dispatched) end-to-end.
status: active
nature: design
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, manifest, availability-index, expected-unattempted, honest-coverage, seeder, design]
related:
  [
    defi_manifest_no_expected_unattempted_seeder_2026_07_26,
    defi_satellite_ao_dispatch_batch2_2026_07_26,
    data_completion_defi_2026_07_15,
    mtds_is_full_adapter_smoketest_findings_2026_07_07,
  ]
created: 2026-07-26
last_updated: 2026-08-01
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [defi_manifest_no_expected_unattempted_seeder_2026_07_26]
source: [defi_satellite_ao_dispatch_batch2-001 (task C8), BLK-7c950d06, BLK-3221d4b3]
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /plans/archive/issues/defi_manifest_no_expected_unattempted_seeder_2026_07_26.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py,
  ]
---

# DeFi expected_unattempted seeder — design

## Background

`defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s C8 todo ("fill DeFi manifest venue-key under-enumeration") was
dispatched to a worker, who found the premise false — see the full re-diagnosis in
[`defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`](issues/defi_manifest_no_expected_unattempted_seeder_2026_07_26.md).
DeFi has no `expected_unattempted` seeder at all; the honest-coverage denominator for lst/lending/perp families is
whatever the union of 3 independently hand-maintained `_DEFAULT_PROTOCOLS` lists happens to cover, not derived from or
cross-checked against UAC's `DEFI_VENUE_DATA_TYPE_CAPABILITIES`/`DEFI_VENUE_PHASE`. Governing SSOT:
`/codex/02-data/honest-absence-downstream-handling.md`.

Two rulings landed 2026-07-26:

- **BLK-7c950d06 → Option A**: build a real seeder mirroring `sentinels.py`'s `record_expected_unattempted`, denominator
  derived from `DEFI_VENUE_DATA_TYPE_CAPABILITIES` + `DEFI_VENUE_PHASE`. The original C8 checkbox CANNOT be completed as
  written and stays unchecked — its disposition is the issue doc's re-diagnosis + this plan.
- **BLK-3221d4b3 → Human plan (assigned_vm: NA), now RESOLVED 2026-07-28**: this plan's own capability-reconciliation
  step was an open-ended per-venue judgment call (not a worker-determinable fact) per the Dispatch-scope-eligibility
  rule (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`), so it had to resolve BEFORE any seeder
  implementation todo became AO-eligible. **Ruling (operator gate-clearance pass, 2026-07-28): disposition (a) — wire
  the existing FLUID-ETHEREUM adapter (`market_interface/adapters/defi/fluid_adapter.py`) into
  `lending_indices_handler.py`'s CLI/manifest-write loop, rather than excluding it from the denominator.** Reasoning:
  the general full-completion mandate for this pass ("all adaptors should be FINISHED with respect to data, unless it is
  literally proven the data cannot be obtained — in which case remove it fully, no half-built adaptors left lying
  around") applies directly here — FLUID-ETHEREUM is NOT a case of unobtainable data: a real, working adapter already
  exists and is already wired into two sibling collectors (risk_params, liquidations); the only gap is that
  lending_indices never got the same wiring. Finishing the wiring (rather than permanently excluding the venue from the
  coverage denominator) is completing an already-established pattern, not new build risk. With this disposition
  resolved, the plan converts to `assigned_vm: planning` and the P0 todo below is DONE.

**Anti-silent-placeholder guardrail (carries through every todo below)**: the seeder must key off ACTUAL collectibility.
No `_DEFAULT_PROTOCOLS` entry (e.g. `fluid`) is ever added without a working collector wired first — doing so would
write a dishonest zero-rows manifest stamp (the exact FLUID failure mode in re-diagnosis finding #5).

## Todos

- [x] ✅ [DATA] P0. **RULED 2026-07-28 (retagged from `[OPERATOR]`) — disposition (a) chosen: wire the existing adapter
      into the manifest-write loop.** Per venue/protocol currently declared in UAC's `DEFI_VENUE_DATA_TYPE_CAPABILITIES`
      / `DEFI_VENUE_PHASE` (`unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py`,
      `defi_venues.py`) but NOT reachable by a working collector today: the FLUID-ETHEREUM case (capability declared,
      real adapter exists at `market_interface/adapters/defi/fluid_adapter.py`, but never wired into
      `lending_indices_handler.py`'s CLI/manifest-write loop — see re-diagnosis finding #5) is resolved as **(a) wire
      the existing adapter into the manifest-write loop** — not (b) exclude-until-collector-exists, since a working
      collector already exists (it's just not wired into this one handler; see Background for full reasoning). Execution
      task: wire `fluid_adapter.py` into `lending_indices_handler.py`'s CLI/manifest-write loop the same way it's
      already wired into the sibling `risk_params`/`liquidations` collectors, verified via a real manifest row for
      FLUID-ETHEREUM lending_indices (not a fabricated placeholder — confirm real fetched data, not a zero-rows stamp).
      If any OTHER venue is found during `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`'s follow-up audit
      todos with the same capability-declared-but-not-wired pattern, apply the same disposition (a) by default per this
      same ruling — treat (b)/exclude as the fallback ONLY if that venue's data is proven genuinely unobtainable (in
      which case remove the capability declaration + adaptor fully rather than leaving it half-wired). Recorded in this
      plan's Progress Log below.
- [x] ✅ [DATA] P1. **Unblocked 2026-07-28 — P0's disposition is now RULED, so this is an ordinary determinable design
      task, no further human judgment required.** Design the seeder itself: a `record_expected_unattempted`-equivalent
      method on `DefiManifestRecorder`
      (`market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py`), fired from a new DeFi
      enumeration pass mirroring `market_tick_data_service/engine/orchestrator/sentinels.py`'s existing
      `record_expected_unattempted` pattern, with denominator = UAC `DEFI_VENUE_DATA_TYPE_CAPABILITIES` +
      `DEFI_VENUE_PHASE` filtered per the P0 reconciliation's dispositions (a FLUID-ETHEREUM lending_indices venue-key
      counts as attempted once its wiring lands, never a venue disposed "exclude until collector exists"). Write the
      design as a doc section here (schema of the new manifest rows, where the enumeration pass hooks into the DeFi
      `collect-*` CLI flow, how it avoids double-counting rows a handler already wrote). Done when: the design section
      is written + reviewed, with no open question about how a disposed-exclude venue is prevented from getting a
      stamped row. — ✅ **Done (2026-07-28, slot 6)**: design written below in
      `## Design — the DeFi expected_unattempted     seeder`. Grounded directly in the current code
      (`_defi_manifest.py`, `sentinels.py`, `defi_venue_capabilities.py`, `defi_venues.py`,
      `lending_indices_handler.py`) — every function/line cited is read, not assumed.
- [x] ✅ [DATA] P2. **Sequentially gated on the P1 design todo above** (an ordinary implementation task once the design
      lands, no further human judgment needed). Implement the seeder per the design, unit-tested, wired into the DeFi
      manifest-write path. Done when: `quality-gates.sh` is green on `market-tick-data-service` and a manifest census
      (deployment-api `_axis_census.py` or equivalent) shows every UAC-declared, non-excluded venue-key carrying at
      least one manifest row (captured or honest `expected_unattempted`) for its declared instrument_type family. — ✅
      **Done (2026-08-01, slot 8)**: `unified-api-contracts@91bafdae` (`get_defi_declared_venues_for_data_type` +
      `DEFI_VENUE_COLLECTIBILITY_EXCEPTIONS`), `market-tick-data-service@a5a93dc0` (`DefiManifestRecorder` seeder
      methods + wiring into `lending_indices`/`liquidations`/`lst_rates`). **Design correction discovered during
      implementation** (see Progress Log + `## Design — the DeFi expected_unattempted seeder` §7 below): the design's
      assumption that `risk_params`/`liquidation_events`/`dex_pools`/`dex_swaps`/`oracle_prices` are venue/chain-grain
      was wrong — they are per-instrument (per-market/per-pool/per-feed) grain in the actual code, so this venue/chain
      seeder is deliberately NOT wired into them (would write an incorrect coarse row); `perp_funding_handler.py` is
      cefi-classified + UAC currently declares zero live DeFi `perp_funding` capabilities, also out of scope. Live
      manifest-census verification (the P2 acceptance's `_axis_census.py` check) is DEFERRED to the next real prod DeFi
      collect-* run — new Todo 4 below tracks it. New Todos 5/6 below track the two adjacent gaps this session surfaced
      (P0's FLUID wiring not actually landed; per-instrument-grain honest-coverage left uncovered).
- [x] ✅ [DATA] P3. **Reclassified 2026-07-27 — sequentially gated on the P2 implementation todo above, NOT itself a
      fresh operator-decision** (a bookkeeping checkbox-flip once the seeder is live, no human judgment needed). Once
      the seeder is live, re-open `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s C8 checkbox and flip it
      referencing this plan + the census evidence (dropping the unsatisfiable DRIFT-SOLANA criterion permanently, per
      the 2026-07-16 operator ruling that removed DRIFT-SOLANA from every UAC registry). — ✅ **Done (2026-08-01, slot
      8), corrected scope**: `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s C8 entry is explicitly a PERMANENT
      non-checkbox (its own text: "intentionally NOT a `- [ ]`/`- [x]` checkbox — it must never be faked `[x]`... the
      superseding plan is the live tracking doc going forward") — this P3 todo's original wording ("re-open...
      checkbox") predates that permanent-supersession decision and is now stale; there is no checkbox to flip. Satisfied
      instead by adding a short prose evidence note to the C8 entry pointing at this plan's P2 completion (same session,
      same turn) — the C8 entry itself stays non-checkbox prose, unchanged in kind.
- [ ] [DATA] P2. **New (2026-08-01, slot 8) — Todo 4, an ordinary verification task, no human judgment needed.** Run the
      P2-above acceptance's live manifest census (deployment-api `_axis_census.py` or equivalent) against a real prod
      `lending_indices`/`liquidations`/`lst_rates` DeFi collect-* run, confirming every `(venue, chain)` returned by
      `get_defi_declared_venues_for_data_type(data_type, as_of=<day>)` carries ≥1 manifest row that day. Done when: the
      census is run + its result (pass/fail + any gap) is recorded in this plan's Progress Log.
- [x] ✅ [DATA] P1. **New (2026-08-01, slot 8) — Todo 5, a bounded implementation task once wired, no human judgment
      needed.** P0's own "Execution task" (wire `fluid_adapter.py` into `lending_indices_handler.py`'s
      CLI/manifest-write loop) was never actually landed —
      `grep -i fluid     market_tick_data_service/cli/handlers/lending_indices_handler.py` returns 0 hits despite P0
      being checked ✅ (only the disposition RULING landed; the Progress Log's 2026-07-28 entry documents the ruling,
      not a wiring commit). This is NOT a P2-above blocker (the seeder's `expected_unattempted` stamp is the honest,
      correct state for FLUID-ETHEREUM lending_indices until it's wired — see the design correction), but the original
      disposition (a) is still unexecuted. Wire it per P0's original spec, verified via a real manifest row for
      FLUID-ETHEREUM lending_indices (not a fabricated placeholder). — ✅ **Done (2026-08-01, slot 14)**:
      `market-tick-data-service@92a6ebb1` — new `lending_indices_fluid.py` dedicated collector (mirrors
      `lending_indices_morpho.py`'s pattern: Fluid has no queryable rate-index subgraph, same as Morpho, so it routes
      past the generic subgraph cascade straight to `FluidAdapter.download_market_data()`'s direct RPC reads via
      `FluidVaultResolver.getVaultEntireData()`); `"fluid"` added to `_DEFAULT_PROTOCOLS`; router in
      `_maybe_dedicated_collector` extended. Verified LIVE against real Alchemy mainnet RPC (not mocked): all 12
      FLUID-ETHEREUM MVP vaults fetched real on-chain data (real block numbers, exchange prices, utilization rates),
      then the full wired collector wrote 1152 real rows across 6 real instrument shards to a real GCS `-test-` bucket
      (`market-data-tick-defi-test-central-element-323112`) — not a zero-rows stamp. Full manifest-row census against a
      real PROD collect-* run is covered by this plan's existing Todo 4 (deferred there, not re-scoped here).
      `quality-gates.sh` green (337s, pyright-suppression ratchet held at frozen baseline via narrow per-line
      `# pyright: ignore[reportPrivateUsage]` instead of a new blanket header). 8 new unit tests in
      `tests/unit/test_lending_indices_fluid.py`.
- [ ] [DATA] P2. **New (2026-08-01, slot 8) — Todo 6, investigation/design task, may need a follow-up plan, no human
      judgment needed to START it.** `risk_params`/`liquidation_events`/`dex_pools`/`dex_swaps`/`oracle_prices` have NO
      venue/chain-level seeder coverage (P2 deliberately excludes them — see the design correction) and their
      per-instrument honest-coverage story is asserted by code comments (`risk_params_handler.py`'s docstring: "~193k
      expected_unattempted cells" from "the v2 expected-universe enumerator
      (instruments-service/scripts/enumerate_expected_universe.py)") but was NOT verified in this session. Investigate
      whether that enumerator actually covers these 5 DeFi data_types today; if it doesn't, design + implement the
      per-instrument analog of this plan's seeder for them (a distinct, larger task — the denominator needs a
      per-instrument catalogue, not just `get_defi_declared_venues_for_data_type`'s venue/chain pairs).

## Design — the DeFi `expected_unattempted` seeder

Grounded in the current code as of 2026-07-28 (`market-tick-data-service`, `unified-api-contracts`). No new file; three
additions to `DefiManifestRecorder` (`market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py`)
plus one new UAC registry helper + one new UAC exception-set constant. No orchestrator-level enumeration pass — DeFi has
no shared cross-handler orchestrator to hook (`engine/orchestrator/__init__.py:413-421` explicitly excludes DeFi venues
from `_build_active_venues_for_date`, routing them to independent `collect-*` CLI handlers instead), so the seeder is
per-handler, mirroring how every DeFi handler already owns its own `DefiManifestRecorder` instance per run.

### 1. Self-tracking on `DefiManifestRecorder` (avoids double-counting without a manifest re-read)

`sentinels.py`'s existing pattern (the CeFi/Sports one this design mirrors) builds its "already captured" set from the
SAME run's in-memory `state.shard_counts` (`_build_captured_shard_sets`, `sentinels.py:109-130`) — it never re-queries
the manifest to dedup. DeFi has no equivalent shared `state` object, but it has something better-suited: every DeFi
handler already funnels every attempt through exactly one `DefiManifestRecorder` instance per run
(`record_captured`/`record_empty`/`record_zero_rows`/`record_failed`, `_defi_manifest.py:165-463`). So:

- Add `self._attempted_keys: set[tuple[str, str, str]] = set()` to `__init__` (`_defi_manifest.py:117-135`).
- At the end of `record_captured` (:165-214), `record_empty` (:264-312 — this also covers `record_zero_rows`, which
  already delegates to `record_empty` at :384-393), and `record_failed` (:428-463), append
  `(normalised_venue, normalised_chain, data_type)` to `self._attempted_keys`, using the SAME `_normalise_venue`/
  `_normalise_chain` helpers `_build_row_key` (:620-667) already calls, so keys compare exactly.

This makes "was this shard attempted this run" a property of the recorder itself — no second manifest read, no
inter-handler coordination, and it composes automatically for any future DeFi data_type that reuses the shim.

### 2. New recorder method: `record_expected_unattempted`

Mirrors `record_zero_rows`'s DeFi-shim kwarg shape (`_defi_manifest.py:348-359`) but delegates to
`ManifestWriter.record_expected_unattempted`
(`unified-trading-library/unified_trading_library/manifest_writer/_writer_record.py:394-459`) instead of `record_empty`:

```python
def record_expected_unattempted(
    self,
    *,
    venue: str,
    chain: str,
    data_type: str,
    pipeline_mode: PipelineMode,
    attempted_at: datetime | None = None,
    instrument_type: str = "",
) -> None:
    """Stamp a UAC-declared, not-yet-attempted-this-run shard as expected_unattempted.
    Only sanctioned caller: emit_expected_unattempted_for_remaining (below) — never
    call this directly for a (venue, chain, data_type) this run already attempted."""
    row_key = _build_row_key(
        target_day=self._target_day, venue=venue, chain=chain,
        data_type=data_type, instrument_type=instrument_type,
    )
    self._writer.record_expected_unattempted(
        row_key=row_key, pipeline_mode=pipeline_mode,
        attempted_at=attempted_at or datetime.now(UTC),
    )
```

Row schema: unchanged v9 `AvailabilityRecord`
(`unified-trading-library/unified_trading_library/manifest_writer/_rows.py:284-486`) —
`capture_status="expected_unattempted"`, `row_count=0`, `error_reason=""` (per
`ManifestWriter.record_expected_unattempted`'s own contract, already exercised by `sentinels.py`; no new field). `chain`
is always populated (the existing A4 `BlankChainError` guard in `_build_row_key`, :651-656, already prevents a
chain-less DeFi row). `instrument_id`/`instrument_type` stay blank for venue/chain-grain data_types (lending_indices,
risk_params, liquidations); a future per-pool-grain data_type would pass `instrument_id` the same way `record_captured`
already does.

### 3. New enumeration method: `emit_expected_unattempted_for_remaining`

```python
def emit_expected_unattempted_for_remaining(
    self,
    *,
    data_type: str,
    declared_venues_chains: Iterable[tuple[str, str]],
    pipeline_mode: PipelineMode,
) -> None:
    """Call once per handler run, right before recorder.close(). Stamps
    expected_unattempted for every UAC-declared (venue, chain) this run never
    attempted for data_type. declared_venues_chains is the CALLER's already-filtered
    denominator (see UAC helper below) — this method does not compute the
    denominator itself, keeping the honest-coverage cross-product logic in ONE
    place (UAC) instead of duplicating a filter per handler."""
    for venue, chain in declared_venues_chains:
        key = (_normalise_venue(venue), _normalise_chain(chain), data_type)
        if key in self._attempted_keys:
            continue
        self.record_expected_unattempted(
            venue=venue, chain=chain, data_type=data_type, pipeline_mode=pipeline_mode,
        )
```

### 4. New UAC denominator helper + exclusion registry (where a disposed-exclude venue is stopped)

New function in `unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py`:
`get_defi_declared_venues_for_data_type(data_type: str, as_of: date) -> list[tuple[str, str]]`. Iterates
`DEFI_VENUE_DATA_TYPE_CAPABILITIES` keys (`defi_venue_capabilities.py:17-24`, `"PROTOCOL-CHAIN"` strings — P2 must reuse
whichever existing UAC helper `_build_defi_venues()` in `defi_venues.py` already uses to parse these keys into
`(venue, chain)` pairs, not hand-roll a new split), keeping only entries where:

1. `DEFI_VENUE_PHASE.get(key) == "live"` (`defi_venues.py:428`, the same filter `market_data_categories.py:411` already
   uses to build the producible venue list — reused, not re-derived);
2. `data_type in DEFI_VENUE_DATA_TYPE_CAPABILITIES[key]` and its declared start_date `<= as_of.isoformat()` (a venue
   whose capability hasn't started yet is honestly out of scope, not "expected");
3. `key not in DEFI_VENUE_COLLECTIBILITY_EXCEPTIONS.get(data_type, set())` — **the new exclusion registry**, a
   `dict[str, set[str]]` constant (data_type → excluded `"PROTOCOL-CHAIN"` keys) added next to `DEFI_VENUE_PHASE`. Empty
   today (the only per-venue judgment call resolved so far — FLUID-ETHEREUM lending_indices — was disposed **(a) wire**,
   not (b) exclude, per this plan's P0). A future venue disposed "(b) exclude — data genuinely unobtainable" (per the
   Background section's disposition rule) gets ONE entry here, commented with the issue-doc/BLK citation that ruled it.

**This is how a disposed-exclude venue is prevented from ever getting a stamped row**: exclusion happens at the
denominator (step 3, inside the UAC helper), not at emission time inside the recorder — an excluded venue is filtered
OUT of `declared_venues_chains` before `emit_expected_unattempted_for_remaining` ever iterates it, so there is exactly
ONE place to check "is this venue excluded for this data_type" (the UAC registry), not a scatter of per-handler
`if venue == "X": continue` checks that could drift out of sync the same way the 3 independent `_DEFAULT_PROTOCOLS`
lists already have (the exact bug class this whole plan exists to fix — see Background).

### 5. Where it hooks into the DeFi `collect-*` CLI flow

Per-handler, inline, immediately before `recorder.close()` — e.g. `lending_indices_handler.py:366`:

```python
recorder.emit_expected_unattempted_for_remaining(
    data_type="lending_indices",
    declared_venues_chains=get_defi_declared_venues_for_data_type("lending_indices", as_of=target_day),
    pipeline_mode=_pm,
)
recorder.close()
```

The SAME pattern applies to every other DeFi `collect-*` handler that already builds a `DefiManifestRecorder`
(`risk_params_handler.py`, `liquidations_handler.py`, and any of dex_pools/dex_swaps/lst_rates/oracle_prices/
perp_funding still to be confirmed at P2) — each stamps its own `data_type`'s denominator against its own
`self._attempted_keys`. No global post-pass is needed or possible: DeFi collect-\* jobs are independent CLI
invocations/VM launches with no cross-handler run-ordering guarantee, so a single global "did every data_type run today"
enumerator would have no reliable trigger point. Per-handler, self-contained enumeration avoids needing one.

### 6. Cross-run dedup (this run's `expected_unattempted` vs. a PRIOR run's real capture)

No special handling needed — identical to `sentinels.py`'s documented behavior.
`ManifestWriter.record_expected_unattempted`'s own docstring (`_writer_record.py:419-421`) already guarantees a later
`record_captured`/`record_empty`/`record_failed` write for the same `row_key` supersedes an earlier
`expected_unattempted` row via the manifest-consolidator's last-writer-wins merge. If FLUID-ETHEREUM lending_indices is
wired (P0) and starts capturing on some future date, that date's `record_captured` call naturally wins over any
`expected_unattempted` stamp a prior day's run may have left for that same key — nothing in this design needs to detect
or clear the earlier row itself.

### P2 acceptance restated against this design

`quality-gates.sh` green + a manifest census showing every `(venue, chain)` returned by
`get_defi_declared_venues_for_data_type(data_type, as_of=<day>)`, for every DeFi data_type, carries ≥1 manifest row
(`captured`, `empty_confirmed`, `attempted_failed`, or `expected_unattempted`) for that day — with zero rows for any
`(venue, chain)` present in `DEFI_VENUE_COLLECTIBILITY_EXCEPTIONS[data_type]`.

### 7. Implementation correction (2026-08-01) — grain scope, not every DeFi data_type

P1's design (written 2026-07-28) implicitly assumed every DeFi `collect-*` handler records manifest rows at venue/chain
grain (`instrument_id` blank). Reading the ACTUAL current code at P2 implementation time found this false for 5 of the 8
handlers that build a `DefiManifestRecorder`:

- **Venue/chain grain (blank `instrument_id`) — SAFE, wired in P2**: `lending_indices_handler.py`,
  `liquidations_handler.py` (data_type `"liquidations"` — note this is a DIFFERENT, currently UAC-undeclared data_type
  from `"liquidation_events"`; the UAC denominator returns `[]` for it today, a harmless no-op, not a bug),
  `lst_rates_handler.py`.
- **Per-instrument grain (`instrument_id` populated) — NOT wired, would be WRONG to wire**: `risk_params_handler.py`
  (per-reserve, `instrument_id=market_id_lower` — its own docstring: "~193k `expected_unattempted` cells" already seeded
  by "the v2 expected-universe enumerator" — a SEPARATE, pre-existing mechanism this plan never touches),
  `liquidation_events_handler.py` (per-market), `dex_pools_handler.py` / `dex_swaps_handler.py` (per-pool),
  `oracle_prices_handler.py` (per-feed). Calling `emit_expected_unattempted_for_remaining` (venue/chain-grain) against
  any of these would write an INCORRECT coarse-grain row alongside their correct per-instrument rows — worse than not
  wiring at all. Per-instrument honest-coverage for these 5 data_types is a separate, larger task (a different
  denominator shape — a declared per-instrument catalogue, not `(venue, chain)` pairs) — tracked as this plan's new
  Todo 6.
- **Excluded — not truly DeFi in this denominator's sense**: `perp_funding_handler.py` is venue/chain grain
  (mechanically safe to wire) but is `asset_group="cefi"` (its own module comment: every protocol in `DEFAULT_PROTOCOLS`
  is cefi-classified) and UAC currently declares ZERO live DeFi `perp_funding` capabilities (GMX's entries were removed
  2026-07-25) — wiring it would be a permanent no-op for a handler that isn't really this plan's DeFi denominator's
  concern, so it was deliberately left out.

## Codex SSOTs

- `/codex/02-data/honest-absence-downstream-handling.md` — governing rule for this whole plan (a genuine absence and an
  unattempted state must never collapse into one signal).
- `/codex/02-data/availability-manifest-and-data-status.md` — manifest/`capture_status` contract the new seeder must
  conform to.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § Dispatch-scope eligibility — why the P0 todo
  was human-only before the 2026-07-28 ruling resolved its disposition.

## Progress Log

- 2026-07-26 (slot 2): Plan created per BLK-3221d4b3's ruling (human plan, `assigned_vm: NA`). No design work started —
  next action is the operator resolving the P0 reconciliation todo.
- 2026-07-28 (operator gate-clearance pass): P0 resolved — **disposition (a)** for FLUID-ETHEREUM lending_indices: wire
  the existing `fluid_adapter.py` into `lending_indices_handler.py`'s manifest-write loop (not
  exclude-from-denominator). Reasoning: the adapter already exists and is already wired into the sibling
  `risk_params`/`liquidations` collectors — this is completing an established pattern, not new build risk, and the
  general full-completion mandate for this pass says finish adaptors rather than leave them half-wired unless the
  underlying data is proven unobtainable (it isn't here). Plan converted `assigned_vm: NA → planning`; P1/P2/P3 are now
  sequentially AO-dispatchable against this disposition.
- 2026-07-28 (slot 6, data_engineering): P1 done. Read `sentinels.py`, `_defi_manifest.py`,
  `defi_venue_capabilities.py`/`defi_venues.py`, `lending_indices_handler.py`, and the parent re-diagnosis issue doc
  directly (via a research sub-agent + targeted follow-up reads) before writing anything, so every function/line the
  design cites is grounded in the current code, not assumed. Wrote `## Design — the DeFi expected_unattempted seeder`
  above: (1) self-tracking `_attempted_keys` set on `DefiManifestRecorder` (avoids a second manifest read for dedup —
  every DeFi attempt already funnels through one recorder instance per run); (2) new `record_expected_unattempted`
  method mirroring `record_zero_rows`'s shape but delegating to `ManifestWriter.record_expected_unattempted`; (3) new
  `emit_expected_unattempted_for_remaining` enumeration method, called once per handler right before `recorder.close()`
  (no global cross-handler pass exists or is needed — DeFi `collect-*` handlers are independent CLI invocations with no
  shared orchestrator, confirmed at `engine/orchestrator/__init__.py:413-421`); (4) new UAC
  `get_defi_declared_venues_for_data_type()` helper + `DEFI_VENUE_COLLECTIBILITY_EXCEPTIONS` registry — this is the
  concrete answer to the "no open question about disposed-exclude venues" requirement: exclusion happens at the
  denominator (one UAC registry), never scattered across per-handler checks, closing off the exact drift pattern (3
  independent `_DEFAULT_PROTOCOLS` lists) this whole plan exists to fix. P2 is now unblocked (its own sequential gate).
- 2026-08-01 (slot 8, data_engineering): P2 done. Implemented the seeder per the P1 design, with one correction found by
  reading the actual handler code before wiring (see `## Design` §7 above): the design assumed every DeFi `collect-*`
  handler is venue/chain grain, but `risk_params`/`liquidation_events`/`dex_pools`/`dex_swaps`/ `oracle_prices` are
  actually per-instrument grain — wiring this venue/chain seeder into them would have written incorrect coarse rows, so
  they were deliberately left unwired (their honest-coverage is a separate, pre-existing per-instrument mechanism this
  plan doesn't touch — investigating whether it's actually complete is new Todo 6). Shipped:
  `unified-api-contracts@91bafdae` (`get_defi_declared_venues_for_data_type` + `DEFI_VENUE_COLLECTIBILITY_EXCEPTIONS`, 7
  unit tests in `tests/unit/test_defi_venue_capabilities.py`) and `market-tick-data-service@a5a93dc0` (3 commits:
  `95d24521` feat — `DefiManifestRecorder._attempted_keys` tracking + `record_expected_unattempted` +
  `emit_expected_unattempted_for_remaining`, wired into `lending_indices_handler.py` / `liquidations_handler.py` /
  `lst_rates_handler.py`, 7 new unit tests in `test_defi_manifest_recorder.py`; `1a2ca97d` test — bumped an UNRELATED
  pre-existing golden shard-count pin (`test_pipeline_e2e_prediction_canonical.py`, DEFI 2700→2727) that Pass-1 QG
  caught red on this exact tree — traced to an already-shipped, unrelated prior-session uac commit (AAVE-PLASMA
  `DEFI_VENUE_PHASE` flip to live), confirmed pre-existing via the exact arithmetic (100→101 live venues × 27 data_types
  = +27), not caused by this session's pure-addition diff; `a5a93dc0` refactor — kept
  `record_captured`/`_finalize_lst_rows` under the repo's 50-line method cap after the seeder wiring pushed them over).
  Both repos' `quality-gates.sh` green (MTDS run hit this shared host's known QG-capacity contention twice — see the
  concurrent `qg_capacity_crisis` issue docs already tracked elsewhere in this corpus — third attempt completed clean at
  530s, sentinel verified == HEAD). Both SHAs verified ancestor-of `origin/live-defi-rollout`. P3's original "flip the
  C8 checkbox" instruction turned out to be stale (that entry was made a PERMANENT non-checkbox 2026-07-26, explicitly
  "must never be faked `[x]`") — satisfied instead with a prose evidence note on the C8 entry itself, pointing back
  here; see `defi_satellite_ao_dispatch_batch2_2026_07_26.md`. Added Todo 4 (live manifest-census verification —
  deferred, needs a real prod DeFi collect-* run, not available from this session), Todo 5 (P0's own "Execution task" —
  wiring `fluid_adapter.py` into `lending_indices_handler.py` — was never actually landed despite P0 reading ✅; not a
  P2-above blocker since `expected_unattempted` is the correct honest state for it either way, but the disposition
  itself is still unexecuted), and Todo 6 (investigate + design the per-instrument analog of this seeder for the 5
  excluded data_types, if their existing per-instrument mechanism turns out incomplete).
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- 2026-08-01 (slot 14, data_engineering): Todo 5 done. Wired `fluid_adapter.py` into `lending_indices_handler.py`'s
  collection loop per P0's original spec. Read the actual code first: `FluidAdapter`'s own docstring already says
  "market-tick-data-service: calls `download_market_data()` for historical data" but a repo-wide grep showed
  `FluidAdapter(` was only ever instantiated in tests — never in production MTDS/instruments-service code. Mirrored the
  existing Morpho dedicated-collector pattern (`lending_indices_morpho.py`) since Fluid has the identical shape: no
  queryable subgraph for rate-index history (its subgraph entry in UAC `SUBGRAPH_IDS` exists only to declare the chain,
  per that dict's own comment — same convention Morpho already uses), so real data only comes from direct RPC via
  `FluidVaultResolver.getVaultEntireData()`, which `FluidAdapter.download_market_data()` already implements. Added
  `market-tick-data-service/market_tick_data_service/cli/handlers/lending_indices_fluid.py` (new
  `_collect_fluid_lending` + `_fetch_fluid_rows`, IS-catalogue-first / adapter-MVP-vault-list fallback, mirroring
  `_collect_morpho_lending`'s IS-first/live-fallback shape), extended `lending_indices_morpho.py`'s
  `_maybe_dedicated_collector` router to also dispatch `protocol == "fluid"`, added `"fluid"` to
  `lending_indices_handler.py`'s `_DEFAULT_PROTOCOLS`. Verification (the P0/Todo-5 anti-fabrication requirement — "not a
  fabricated placeholder... confirm real fetched data, not a zero-rows stamp"): ran the wired collector twice against
  LIVE Alchemy mainnet RPC (`unified-trading-sa` GCP identity, `alchemy-api-key` GSM secret) — (1) a standalone
  `FluidAdapter.download_market_data()` call returned 96 genuine on-chain samples (real block numbers, real
  supply/borrow exchange prices, real utilization rates) for one MVP vault; (2) the full wired
  `_collect_fluid_lending()` path, run with `IS_TEST_RUN=true` (routes writes to
  `market-data-tick-defi-test-central-element-323112`, never prod), fetched all 12 FLUID-ETHEREUM MVP vaults (IS
  catalogue already had 12 stamped Fluid instruments — A_TOKEN/DEBT_TOKEN pairs sharing 6 real vault addresses) and
  wrote 1152 real rows across 6 real parquet shards (verified via GCS blob listing: real byte sizes ~17.5KB each, not
  zero-byte placeholders) — `market_count_map` returned 6 real vault addresses each with 192 real captured rows, exactly
  the shape `record_market_captures` would use for a real `record_captured` manifest row per vault. Did NOT additionally
  round-trip a live `DefiManifestRecorder` write in this session (would need `VM_NAME`/manifest-shard plumbing beyond
  this todo's scope) — full manifest-row CENSUS verification against a real PROD collect-* run stays covered by this
  plan's existing Todo 4, unchanged. One real QG finding surfaced + fixed during this work: the new file's
  `result.get("lending_indices", [])` pattern hit the empty-dict/list-fallback fail-fast gate (fixed with a justified
  `# noqa: qg-empty-fallback` — `FluidAdapter.download_market_data()` genuinely has early-return branches that return
  `{}` with no `"lending_indices"` key at all, unlike Morpho's fail-fast contract); and the file's originally-copied
  blanket `# pyright: ...` header pushed the STEP 5.94 pyright-suppression-header ratchet baseline from 237→238 (net-new
  broad suppressions banned) — replaced with 2 narrow per-line `# pyright: ignore[reportPrivateUsage]` comments instead,
  ratchet held at 237. Shipped: `market-tick-data-service@92a6ebb1` (4 files: new `lending_indices_fluid.py`, new
  `tests/unit/test_lending_indices_fluid.py` — 8 unit tests covering IS-catalogue-first/MVP-fallback routing,
  empty-markets short-circuit, per-vault exception isolation, and the FluidAdapter early-return-empty-dict contract —
  - edits to `lending_indices_handler.py`/`lending_indices_morpho.py`). `quality-gates.sh` green (337s, Pass-1 sentinel
    == committed HEAD). SHA verified ancestor-of `origin/live-defi-rollout`.
