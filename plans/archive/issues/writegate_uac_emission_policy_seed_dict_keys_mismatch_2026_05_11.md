---
doc_type: issue
title: writegate UAC SERVICE_OUTPUT_POLICIES seed dict — MDPS service-name typo + book_snapshot_5 key shape blocks slice (b) POC + Phase 6.2
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-data-processing-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-11
author: ikenna-slot8-phase6-2-mdps-wiring
source: ['unified-api-contracts/unified_api_contracts/canonical/crosscutting/service_emission_policy.py:163-168', 'market-data-processing-service/market_data_processing_service/app/core/canonical_writer.py:479', unified-trading-pm/plans/archive/2026_05/writegate_honest_coverage_endtoend_2026_05_06.md Phase 6.2 (line 3119-3126), unified-trading-pm/plans/archive/2026_05/writegate_honest_coverage_endtoend_2026_05_06.md slice (b) Phase 5.3-5.4]
locked_by: live-defi-rollout
locked_since: 2026-05-11
---

# writegate UAC SERVICE_OUTPUT_POLICIES seed dict — MDPS service-name typo + book_snapshot_5 key shape blocks slice (b) POC + Phase 6.2

> **Status (2026-05-11 PM)**: ✅ RESOLVED. Bug 1 fixed at `UAC@7be6bd5` (seed-dict rename) + `UTL@4d8de4ce` (docstring
> sweep). Bug 2 decision (option α) codified at `PM@fa806abe` (CLAUDE.md "Service-output emission policy" section
> extended). Regression guard at `MDPS@daf9988` (8 new tests under `TestServiceEmissionPolicySeedRuntimeLookup` hit the
> REAL UAC seed dict — no mocks). All 4 commits FF-pushed to `origin/live-defi-rollout`. Phase 6.2 wiring is now
> unblocked. Closes this issue.

> **Severity**: P0 — silently-broken slice (b) POC + blocks slice (c) Phase 6.2 wiring on the only available
> per-data_type seed. **Blast radius**: unified-api-contracts (1 file, 6 keys) + market-data-processing-service (slice
> (b) POC at `canonical_writer.py:479` + 17 tests at `tests/unit/test_canonical_writer_ohlcv_1h_policy.py:199`) +
> writegate plan Phase 6.2 (downstream wiring depends on resolution). **Suggested owner**: writegate plan author
> (operator triage — closed-set design call on service-name + key-shape convention before any further wiring lands).

## What I found

Surfaced 2026-05-11 ~16:00 UTC while bootstrapping Phase 6.2 (wire `publish_with_manifest_lookup` at MDPS
`ohlcv_1m:current` / `ohlcv_1m:historical` / `ohlcv_24h` / `book_snapshot_5`). Two distinct seed-dict bugs that silently
break the runtime policy lookup:

### Bug 1 — Service-name typo in UAC seed dict (`pipeline` vs `processing`)

UAC `unified_api_contracts/canonical/crosscutting/service_emission_policy.py:163-168` declares the 6 MDPS seed entries
with `"market-data-pipeline-service"` as the service-name key:

```python
SERVICE_OUTPUT_POLICIES: Final[dict[tuple[str, str], ServiceEmissionPolicy]] = {
    ("market-data-pipeline-service", "ohlcv_1m:current"): ServiceEmissionPolicy.STRICT_FAIL,
    ("market-data-pipeline-service", "ohlcv_1m:historical"): ServiceEmissionPolicy.PARTIAL_OK,
    ("market-data-pipeline-service", "ohlcv_1h:current"): ServiceEmissionPolicy.STRICT_FAIL,
    ("market-data-pipeline-service", "ohlcv_1h:historical"): ServiceEmissionPolicy.PARTIAL_OK,
    ("market-data-pipeline-service", "ohlcv_24h"): ServiceEmissionPolicy.PARTIAL_OK,
    ("market-data-pipeline-service", "book_snapshot_5"): ServiceEmissionPolicy.STRICT_FAIL,
    ...
```

But the **canonical workspace service-name is `market-data-processing-service`** — verified at:

- `market-data-processing-service/market_data_processing_service/app/core/data_source.py:153`:
  `service_name="market-data-processing-service"` (ServiceBootstrap setup).
- All `ServiceBootstrap(...)` + `ManifestWriter(service_name=...)` + `log_event` callers in MDPS source use
  `market-data-processing-service` (8 callsites grep'd).
- The slice (b) POC at `canonical_writer.py:479`:
  `publish_with_manifest_lookup(service="market-data-processing-service", output_data_type="ohlcv_1h:current", ...)`.
- The slice (b) POC unit tests at `tests/unit/test_canonical_writer_ohlcv_1h_policy.py:199`:
  `assert kwargs["service"] == "market-data-processing-service"`.

**Net effect**: every runtime `publish_with_manifest_lookup` call from MDPS resolves through
`get_emission_policy(service="market-data-processing-service", output_data_type=...)`. The dict lookup MISSES (key shape
`("market-data-processing-service", ...)` is absent from the seed) and falls through to the `STRICT_FAIL` default at
`service_emission_policy.py:228`. The slice (b) POC therefore behaves as STRICT_FAIL for both `:current` AND
`:historical` slices — even though the operator-msg-10 framing AND the UAC seed AND the codex SSOT all explicitly say
`:historical` SHOULD be `PARTIAL_OK`. The `:current` STRICT_FAIL is a coincidence that the two policies happen to agree;
`:historical` is a real semantic difference (`PARTIAL_OK` would publish a degraded row + `PUBLISHED_DEGRADED` event;
STRICT_FAIL default skips the row + `STALE_DATA` event).

Provenance of the typo: UAC@`58c3b61` (2026-05-08 17:14 UTC) introduced the file with `market-data-pipeline-service`.
Re-using the term "market-data-pipeline" elsewhere in the workspace returns 0 hits (verified via
`grep -rn "market-data-pipeline-service" --include='*.py' .tabs/8/`). It's a one-off typo at the original ship — not a
deliberate naming convention.

### Bug 2 — `book_snapshot_5` seed key shape mismatch with MDPS `mdps_dt` post-mapping

MDPS `canonical_writer.py:76` defines `_SOURCE_OHLCV_PREFIX = {"book_snapshot_5": "book5_ohlcv"}`. The
`mdps_data_type_key("book_snapshot_5", tf)` mapping at `canonical_writer.py:103` produces:

- `mdps_data_type_key("book_snapshot_5", "1m")` → `"book5_ohlcv_1m"`
- `mdps_data_type_key("book_snapshot_5", "5m")` → `"book5_ohlcv_5m"`

The UAC seed key `("market-data-pipeline-service", "book_snapshot_5")` doesn't match the post-mapping `mdps_dt` shape.
Two reconciliation paths, both architectural decisions:

- **(α)** UAC key reflects the **source data_type** (the operator-thinks-about token) → `"book_snapshot_5"` stays, but
  the slice (b) `_is_ohlcv_1h_aggregation_path`-style gate function for book_snapshot_5 must pass
  `output_data_type="book_snapshot_5"` (NOT the mdps_dt `book5_ohlcv_1m`). Consistent with how slice (b) passes
  `"ohlcv_1h:current"` (matches the source-conceptual data_type, NOT the runtime mdps_dt which is also `"ohlcv_1h"` in
  that case so the issue doesn't surface).
- **(β)** UAC key reflects the **emitted data_type** (post-mapping `mdps_dt`) → seed dict should have entries for each
  `book5_ohlcv_<tf>` cadence (`book5_ohlcv_1m`, `book5_ohlcv_5m`, `book5_ohlcv_15m`, `book5_ohlcv_1h`,
  `book5_ohlcv_24h`). That's a 5x expansion of the book_snapshot_5 seed rows. Could optionally collapse via slice
  differentiation (`book5_ohlcv:current` / `:historical`) if the policy is timeframe-independent.

Either (α) or (β) is a design decision the writegate-plan author owns. Both are workable; both have implications for
slice (c) Phase 6.3-6.8 per-service rollout shape.

### Why slice (b) POC didn't catch this

Slice (b) shipped 17 unit tests (`tests/unit/test_canonical_writer_ohlcv_1h_policy.py`). The tests mock
`publish_with_manifest_lookup` entirely (`patch.object(canonical_writer, "publish_with_manifest_lookup", ...)`) and only
assert the kwarg shape — they never actually run the lookup against the UAC seed. So the
`service="market-data-processing-service"` arg looks correct in the test (matches the slice (b) author's intent) and the
test passes — but the runtime behaviour against the real UAC dict is the broken STRICT_FAIL default. The integration
test (`Phase 5.4 P1 30-day integration test`) per the writegate plan is **DEFERRED** to the post-Phase 6.2 timeline,
which is why this hadn't surfaced before today.

## Why it matters

1. **Slice (b) POC is silently-degraded.** The `:historical` PARTIAL_OK semantics never fire — every gappy backfill row
   routes through the STRICT_FAIL default → heartbeat-only STALE_DATA event → no manifest row. For the May-23 live-DeFi
   cutover, `:historical` backfills of `ohlcv_1h` need to PUBLISH degraded rows with `completeness_fraction` so
   downstream consumers (features-volatility, ml-training, strategy backtest) can branch on coverage. STRICT_FAIL on
   `:historical` looks like "missing data" to those consumers.
2. **Phase 6.2 wiring would inherit the same bug if I proceed without fixing.** I'd add 4 more
   `publish_with_manifest_lookup` callsites that all silently fall through to STRICT_FAIL — including
   `ohlcv_24h:PARTIAL_OK` and the `book_snapshot_5` row whose key shape is ambiguous regardless.
3. **Slice (c) per-service rollout (Phase 6.3-6.8) is gated on a correct seed-dict naming convention.** Feature
   services + ml-training + strategy / execution will all reference the seed using their own canonical service-name
   ("features-volatility-service", "ml-training-service", etc.). The MDPS typo establishes a precedent — agents wiring
   those services need to know whether to use the exact service-name from their ServiceBootstrap or some alternate
   convention.
4. **CLAUDE.md "Service-output emission policy" rule (cited at line 442 of the workspace-canonical CLAUDE.md) directly
   references the UAC seed as authoritative**, with the example `service="market-data-pipeline-service"` in the
   docstring at `emission_publisher.py:127`. The doc + the seed agree on the typo; the actual workspace service-name
   disagrees with both.

## Recommended decision

### Recommended path (option a)

**Fix UAC seed-dict (1 file change, 6 keys):** rename every `"market-data-pipeline-service"` to
`"market-data-processing-service"`. Plus update the helper docstring example at `service_emission_policy.py:127`

- `service_emission_policy.py:216`. Plus update the `publish_with_policy` docstring example at
  `unified-trading-library/unified_trading_library/emission_publisher.py:127` + `:267`. Plus update CLAUDE.md key-rule
  prose at the "Service-output emission policy" section. Plus update the writegate plan body's slice-(b) Phase 5.2 +
  Phase 5.6 anywhere it cites the example. ~10 surgical edits across UAC + UTL + CLAUDE.md + writegate plan, no semantic
  change other than the typo fix.

**For Bug 2 (book_snapshot_5)**, recommend **option (α)** — UAC key stays at the source-conceptual data_type level
(`"book_snapshot_5"`), Phase 6.2 wiring passes `output_data_type="book_snapshot_5"` directly when
`source_data_type == "book_snapshot_5"`, the gate function `_is_book_snapshot_aggregation_path` checks
`source_data_type == "book_snapshot_5"` (NOT the post-mapping `mdps_dt`). Consistent with slice (b) shape; minimal
seed-dict churn; preserves the operator-msg-10 "5 policies seeded for MDPS" framing.

### Why this is operator-triage, not "Clear context = implement"

- Touches UAC public API surface (key shape in the SSOT). Per CLAUDE.md "Citadel-Grade Planning § 7 Single Source of
  Truth" — UAC seed naming convention is a workspace contract.
- Retroactively changes the slice (b) POC commit message + test assertions (commit `MDPS@9e1a93e` references
  `"market-data-processing-service"` in its docstring + tests; if the operator picks (β) the test assertions need to
  update; if the operator picks (α), no MDPS code changes but the UAC + CLAUDE.md + UTL doc rewrites are still
  closed-set design calls).
- Affects the work-split: if `:current` STRICT_FAIL is the seed-dict default-coincidence, do we want to leave the
  default-fallback at STRICT_FAIL forever (current shape) or make get_emission_policy raise on unseeded pairs? Different
  agents wiring slice (c) will branch on this.
- Cross-side coordination: writegate slice (b) was the cross-side handshake delivery for slot 6 / harsh. Both sides'
  rollout depends on the seed-dict naming convention staying stable from this point forward.

### What I'm doing while BLOCKED

Per the conditional-push rule, NOT touching code while Q is open. Slot 8's Phase 6.2 wiring is paused. Will continue
read-only context (audit MDPS adapter sites where `ohlcv_1m` / `ohlcv_24h` / book_snapshot routes through, since the
wiring touchpoints don't change between options (α) and (β)).

Operator triage routing: this could fold into the writegate plan directly as a Phase 6.0 prerequisite (UAC seed
canonicalisation before Phase 6.2 wiring), OR it could ship as a standalone 30min ratchet PR — both shapes are fine.

## Composes with

- `writegate_honest_coverage_endtoend_2026_05_06.md` slice (b) Phase 5.3-5.4 + slice (c) Phase 6.2 (this issue blocks
  Phase 6.2 directly + retroactively touches Phase 5.3-5.4 POC).
- `manifest_schema_final_gate_2026_05_09.md` Phase 1 (column declaration — different concern, unaffected by this bug per
  the slice-(b) Q1 resolution scope decision).
- CLAUDE.md "Service-output emission policy" key-rule section (cites
  `unified_api_contracts.canonical.crosscutting.service_emission_policy.SERVICE_OUTPUT_POLICIES` as authoritative; the
  typo + key-shape bug make the doc inconsistent with itself).
