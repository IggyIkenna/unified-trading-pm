---
doc_type: issue
title: >-
  depth_of_book_10 is live-captured to the central event-log warm sink but has no SINK_MATRIX entry — contract gap
  surfaced by batch13 archival
summary: >-
  `cefi_satellite_ao_dispatch_batch13_2026_08_09.md` todo 2 (verified 2026-08-10: 1,743 warm parquet objects + 9,156
  manifest rows across all 5 capable venues) wired `depth_of_book_10` into the CeFi live event-log capture path, and a
  `persist_cefi_depth_of_book_10` Pub/Sub topic + `warm_sink_persist_cefi_depth_of_book_10` GCS warm-sink subscription
  were added to `deployment-service/terraform/gcp/live_event_log/` (whose header claims it is generated from
  `unified_api_contracts.events.sink_matrix.SINK_MATRIX`). But `SINK_MATRIX` itself has NO `("cefi",
  "depth_of_book_10")` entry (it has cefi `trades`/`book_snapshot_5`/`derivative_ticker`/`liquidations` only) —
  violating the module's own contract: "every live (asset_group, data_type) shard that publishes to the Pub/Sub central
  log must have an entry… New connectors that add a shard MUST add a SINK_MATRIX entry before going live (enforced by
  the completeness gate in tests/unit/test_sink_matrix_completeness.py)". The referenced completeness-gate test does not
  exist at that path in unified-api-contracts. Found during the batch13 finalize archival's codex-alignment step
  (2026-08-10).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [unified-api-contracts, deployment-service]
scope: [engineer]
tags: [cefi, depth-of-book-10, sink-matrix, event-log, contract-gap, data-correctness]
related:
  [
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch13_2026_08_09.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
  ]
created: "2026-08-10"
author: slot-6
last_updated: "2026-08-10"
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
source: >-
  Found 2026-08-10 (slot-6) during the cefi_satellite_ao_dispatch_batch13_2026_08_09_finalize.md archival ritual's
  step-3 codex-alignment check — direct read of `unified_api_contracts/events/sink_matrix.py` (no ("cefi",
  "depth_of_book_10") entry) vs `deployment-service/terraform/gcp/live_event_log/{main.tf,warm_sink.tf}` (topic +
  warm-sink subscription present).
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
---

# depth_of_book_10 missing from SINK_MATRIX (live shard, no contract entry)

## What I found

`cefi_satellite_ao_dispatch_batch13_2026_08_09.md` todo 2 wired `depth_of_book_10` into the CeFi live event-log capture
path for the 5 capable venues (COINBASE-SPOT, BYBIT, DERIBIT, BINANCE-FUTURES, OKX-SWAP), verified 2026-08-10 with 1,743
warm parquet objects landing under `gs://central-element-323112-events/live-events/warm/cefi/depth_of_book_10/` and
9,156 availability-index rows. The Terraform that provisions the warm sink
(`deployment-service/terraform/gcp/live_event_log/{main.tf,warm_sink.tf}`, headers: "Generated from
unified_api_contracts.events.sink_matrix.SINK_MATRIX (52 entries)" / "Cloud Storage subscriptions (warm sink) for all 52
SINK_MATRIX shards") carries a `persist_cefi_depth_of_book_10` topic (main.tf:481) and
`warm_sink_persist_cefi_depth_of_book_10` subscription (warm_sink.tf:905).

But `unified_api_contracts/events/sink_matrix.py` — the SSOT those headers name as the generator source — has **no
`("cefi", "depth_of_book_10")` entry**. Its cefi block is exactly: `trades` (73), `book_snapshot_5` (74),
`derivative_ticker` (75), `liquidations` (76); the only depth-shaped entry is the cross-cutting
`("*", "book_depth_bands")` (108), a different data_type. The module docstring is unambiguous: "Every live (asset_group,
data_type) shard that publishes to the Pub/Sub central log must have an entry here" and "New connectors that add a shard
MUST add a SINK_MATRIX entry before going live (enforced by the completeness gate in
tests/unit/test_sink_matrix_completeness.py)". That completeness-gate test file does not exist at the referenced path in
unified-api-contracts (checked 2026-08-10).

**Net effect**: the warm-sink subscription for `depth_of_book_10` was created in Terraform without the SINK_MATRIX entry
the module requires, so the shard is live with no retention/class/table config in the registry — and the "enforced"
completeness gate that should have caught it is absent. Whether this is (a) a missing SINK_MATRIX entry, (b) a
deliberate exemption that should be documented + the Terraform header corrected, or (c) an accidental hand-edit of the
generated Terraform is NOT determined here — the fix is bounded and checkable either way.

## Why it matters

SINK_MATRIX drives retention class, warm/cold GCS TTL, and sink enablement for the live=batch event-log spine
(`/codex/02-data/live-data-persistence-and-event-log.md`). A live shard outside the matrix means its retention/lifecycle
policy is ungoverned (or governed by an unintended default), and future regenerations of the Terraform from SINK_MATRIX
would silently drop the depth_of_book_10 topic/subscription that production currently relies on.

## Recommended decision

- [ ] [DATA] P2. **Reconcile SINK_MATRIX with the live depth_of_book_10 shard** — either (a) add
      `("cefi", "depth_of_book_10"): SinkConfig(REPRODUCIBLE, ...)` to `unified_api_contracts/events/sink_matrix.py` (+
      any needed completeness-gate coverage), or (b) if the warm-sink subscription is intentionally exempt from
      SINK_MATRIX, document the exemption in the module docstring + correct the Terraform headers' "generated from
      SINK_MATRIX" claim. Verify: `retention_class_for(("cefi","depth_of_book_10"))` and
      `sinks_for(("cefi","depth_of_book_10"))` resolve without KeyError, and the regenerated Terraform keeps the
      production topic/subscription. Repos: unified-api-contracts + deployment-service (regen check only).
- [ ] [DATA] P3. **Reconcile the missing `test_sink_matrix_completeness.py`** referenced by `sink_matrix.py`'s docstring
      as the shard-completeness gate — either locate/restore it, or correct the docstring to name the actual gate (or
      remove the claim if the gate was retired). Repo: unified-api-contracts.

## Progress Log

- **slot-6 2026-08-10 (data_engineering, batch13 finalize archival)**: Filed during the batch13 archival ritual's step-3
  codex-alignment check. Direct reads: `sink_matrix.py` (no depth_of_book_10 entry; cefi block = 4 data_types),
  `deployment-service/terraform/gcp/live_event_log/main.tf:481` + `warm_sink.tf:905` (topic + subscription present),
  completeness-test path absent. Not fixed inline — bounded follow-ups above. Batch13 archived in the same session.
