---
doc_type: codex-ssot
title: Multi-Mode Wallet Isolation — Paper + Live on Shared Wallet
summary:
  "Paper and live running on the same wallet stay isolated via a PBMS virtual-ledger overlay (Option B) — on-chain
  positions are live-only, paper positions tracked off-chain and tagged CanonicalPosition.mode=paper; _live_positions
  and _paper_positions MUST never be summed and paper margin is always 0. Post-cutover migrates to venue sub-accounts."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [execution, defi, cefi, reconciliation, live-trading, ssot]
related:
  [
    /codex/04-architecture/operational-modes.md,
    /codex/04-architecture/paper-vs-live-execution-seam.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
  ]
created: 2026-05-15
authoritative_for: [paper-live shared-wallet isolation, PBMS virtual-ledger overlay, CanonicalPosition mode tagging]
referenced_by:
owner: topology_qgroup_gap_closure_2026_05_09 Phase 4
last_reviewed: 2026-09-03
code_refs:
updated: 2026-05-15
closes: GAP-13
---

# Multi-Mode Wallet Isolation

> **⚠️ DESIGN DECISION — NOT YET IMPLEMENTED (verified 2026-07-31 freshness re-review).** The decision below stands, but
> nothing in § "Implementation Contract" / § "Integration Test Gate" is shipped. Measured against the current tree:
>
> | Doc claim                                                          | Reality                                                                                                                             |
> | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
> | `CanonicalPosition.mode` field                                     | **Does not exist.** `unified_api_contracts/canonical/domain/position/__init__.py::CanonicalPosition` has no `mode` field.            |
> | PBMS `_live_positions` / `_paper_positions` split ledgers          | **Not implemented** anywhere in `strategy_service/position/`.                                                                        |
> | `execution-service/tests/integration/test_multi_mode_wallet_isolation.py` | **Does not exist.** The "gates the May-23 ramp" claim never had a gate behind it.                                              |
> | "position-balance-monitor (PBMS)" as a standalone service          | **Retired 2026-05-20** — subtree-merged into `strategy-service` as the `strategy_service/position/` sub-package (SSOT [`/codex/04-architecture/strategy-service-architecture.md`](/codex/04-architecture/strategy-service-architecture.md)). Read every "PBMS" below as that sub-package. |
> | Paper positions "written to BigQuery"                              | **Stale storage claim** — BigQuery dual-write was removed; all production data lands in GCS Parquet (SSOT [`/codex/02-data/hive-schema-compatibility.md`](/codex/02-data/hive-schema-compatibility.md)). |
>
> Treat this doc as the design record for the shared-wallet isolation approach, **not** as a description of shipped
> behaviour. Anything building on it must implement the contract first.

## Decision (2026-05-15)

**Selected approach: virtual ledger overlay (Option B)**

When paper and live modes run simultaneously on the same wallet, position-balance-monitor (PBMS) tracks paper positions
off-chain via a virtual ledger overlay. On-chain positions belong exclusively to the live mode. Paper positions are
accounted in PBMS memory + emitted as `CanonicalPosition` records tagged `mode=paper`.

**Rationale for Option B over Option A (separate sub-accounts)**:

- May-23 target venues (Binance, Bybit, OKX) all support sub-accounts, but provisioning + permission setup takes 3-5
  business days per venue — too late for May-23.
- Virtual ledger works on any venue without new account provisioning.
- Off-chain paper position tracking is auditable: every paper position record is persisted with the same schema as live
  fills, enabling post-hoc parity analysis. (The 2026-05-15 text said "written to BigQuery" — the storage target is now
  GCS Parquet; BigQuery dual-write no longer exists.)

**Post-cutover (June+)**: migrate to sub-account isolation (Option A) once provisioning is complete. Sub-accounts give
cleaner on-chain audit trails and simplify margin attribution.

## Implementation Contract

### CanonicalPosition mode tag

**TARGET, not shipped** — `CanonicalPosition` currently has no `mode` field; adding it to
`unified_api_contracts/canonical/domain/position/__init__.py` is step 1 of implementing this doc.

`CanonicalPosition.mode` (str): `"live"` | `"paper"`. The position sub-package writes all positions with the `mode`
field set. Downstream consumers (risk sub-package, analytics) MUST filter by mode before aggregating exposure.

### PBMS split rule

**TARGET, not shipped.** The position sub-package maintains two independent position ledgers per instrument per venue:

- `_live_positions: dict[str, Decimal]` — derived from real fills (CanonicalFill stream)
- `_paper_positions: dict[str, Decimal]` — derived from simulated fills (BatchMatchingEngine output)

Live and paper ledgers MUST NOT be summed together. Any code path that aggregates positions without a mode filter is a
correctness bug.

### Fill routing

| Fill source                                     | Destination ledger | Mode tag on CanonicalPosition |
| ----------------------------------------------- | ------------------ | ----------------------------- |
| Live exchange (CanonicalFill via venue adapter) | `_live_positions`  | `"live"`                      |
| BatchMatchingEngine (simulated fill)            | `_paper_positions` | `"paper"`                     |

### Risk service

Risk-and-exposure service queries PBMS with `mode` filter. The carry_staked_basis live archetype queries `mode=live`
only. Paper archetype queries `mode=paper` only. Operator dashboards show both, labelled.

### Margin attribution

Live margin is computed from `_live_positions` only. Paper archetype has no real margin impact — PBMS returns
`margin_used=Decimal("0")` for all paper positions. This simplifies margin accounting: the live archetype owns 100% of
actual margin.

## Integration Test Gate

**NOT BUILT** — this file does not exist in `execution-service`. The May-23 dual-mode launch shipped without it, so the
"without green, the dual-mode launch is blocked" line below was never an enforced gate. Kept as the spec for the test
whoever implements the contract must write.

`execution-service/tests/integration/test_multi_mode_wallet_isolation.py` MUST:

1. Inject two fills for the same instrument: one from the live fill stream, one from BatchMatchingEngine
2. Assert PBMS `_live_positions` contains only the live fill delta
3. Assert PBMS `_paper_positions` contains only the simulated fill delta
4. Assert `CanonicalPosition(mode="live")` and `CanonicalPosition(mode="paper")` are emitted separately
5. Assert live margin attribution excludes paper positions

This test was specified to gate the May-23 carry-live + funding-arb-paper ramp.

## Post-Cutover Migration Path

After June-1 sub-account provisioning:

1. Provision sub-accounts at each venue (Binance `PAPER_<strategy_id>`, Bybit `PAPER_<strategy_id>`)
2. PBMS switches to reading real sub-account balances for paper mode instead of virtual ledger
3. Virtual ledger is retired; `_paper_positions` dict removed
4. `CanonicalPosition.mode` field remains — now sourced from sub-account label

Migration plan to be written when sub-account provisioning completes.
