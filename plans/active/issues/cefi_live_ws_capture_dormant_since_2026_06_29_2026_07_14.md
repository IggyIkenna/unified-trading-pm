---
doc_type: issue
title:
  CeFi live WS tick capture (book_snapshot_5/trades/depth_of_book_10) has produced no manifest rows since 2026-06-29 —
  appears fully dormant
summary: >
  While verifying l2_book_microstructure_capture_2026_07_13 todo 7's done-condition ("the feed is honestly live for the
  capable venues"), found the availability manifest has ZERO live_* pipeline_mode rows after 2026-06-29 (15 days stale)
  across EVERY CeFi live data_type checked (book_snapshot_5, trades, depth_of_book_10, queue_position) and EVERY venue
  checked — not just the 5 depth_of_book_10-capable venues this plan targets. No running compute instance in the project
  looks like a persistent live-WS process (every RUNNING instance is a bounded backfill/batch job); no GKE clusters
  exist. This looks like the entire CeFi live tick-capture pipeline stopped running 15 days ago, not a
  data-type-specific gap.
status: open
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [live-capture, data-correctness, big-finding, orderbook]
related: [l2_book_microstructure_capture_2026_07_13.md]
created: 2026-07-14
parent_epic: strategy_master
priority: P1
source:
  [
    "Discovered while dispatched l2_book_microstructure_capture-007 (slot 11, 2026-07-14) — checking whether todo 7's
    done-condition ('the feed is honestly live for the capable venues') was actually satisfied before flipping it.",
  ]
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-14
locked_by:
resolved_by:
---

# CeFi live WS tick capture appears dormant since 2026-06-29

## What I found

Investigating whether `l2_book_microstructure_capture_2026_07_13.md` todo 7's done-condition ("the feed is honestly live
for the capable venues") was actually true before flipping its checkbox, I checked the availability manifest (via
`read_availability_index` — bounded, not a raw GCS walk) for `depth_of_book_10`:

- **0 rows ever captured** for `depth_of_book_10` (any venue, any status) — todo 2's live connectors
  (`market-tick-data-service@15f5657b`) have shipped but apparently never actually been dispatched.

Widening the check to `book_snapshot_5` (the FOUNDATION this whole plan builds on — "the 9 CeFi venues currently
carrying `book_snapshot_5`") found something bigger:

- Most-recent genuinely `captured` `book_snapshot_5` row, across ALL venues: **2026-05-22**. Per-venue it's often much
  staler (COINBASE-SPOT: 2026-02-05, OKX-SWAP: 2026-03-01, DERIBIT: 2026-04-14).
- Widening further to EVERY `live_*`-pipeline_mode manifest row (any venue, any CeFi data_type — trades,
  book_snapshot_5, derivative_ticker, etc.), not just book/microstructure: the newest row in the ENTIRE manifest is
  **2026-06-29** (15 days stale as of this check), and even those last rows are `empty_confirmed`, not real captures.
- Cross-checked via GCS directly (bounded single-path checks, not a recursive walk): `day=2026-07-14` has **no objects
  at all** in the CeFi tick bucket; `day=2026-07-13`/`07-10`/`07-01`/`06-15` each have `pipeline_mode=batch_*`
  directories only (Deribit/Extended/Tardis/Aster/Hyperliquid batch jobs) — **no `pipeline_mode=live_*` directory
  appears in any of the 4 recent days sampled**.
- `gcloud compute instances list` (project-wide, no name filter) shows every currently-`RUNNING` instance is a bounded
  backfill/batch job (`af-backfill-*`, `cefi-*-heavy/light` batch, `tradfi-bf-*`, `features-sports-*`,
  `mtds-dex-pools-backfill`) — nothing that looks like a persistent live-WS listener. No GKE clusters exist in the
  project either.

**This reads as the entire CeFi live tick-capture pipeline (not just `depth_of_book_10`, not just this plan's 5 venues)
having stopped running roughly 15 days ago**, not a narrow data-type gap. I have NOT root-caused why (no access to
whatever deployment mechanism the live process normally runs under — Compute Engine instance group, supervisor/systemd
unit on a host outside this project's `gcloud compute instances list` view, a manually-launched tmux/screen session,
etc.) or confirmed this is not somehow expected (e.g. an intentional pause I'm not aware of).

## Why it matters

Per the workspace HARD RULE ("Data pipeline correctness is the heartbeat... a RED data audit FREEZES layer-N+1 work"),
this is exactly the class of finding that should NOTIFY OPERATOR, not just get quietly logged: CeFi live market data
(order books, trades) is a foundational input to strategy-service, execution-service, features-service, and every
downstream engine that reads live CeFi ticks — if it has genuinely been offline 15 days, that is a much bigger blocker
than this plan's `queue_position` feature work, and likely affects live/paper trading fidelity for CeFi right now
(batch=live determinism assumes both actually run).

I have NOT attempted to restart/relaunch anything — this needs operator awareness of what the correct live-capture
deployment target is before anyone dispatches it back up (risk of duplicating capture, wrong config, or masking a
deliberate pause I don't have context on).

## Recommended decision

**Operator/main confirms**: (1) is CeFi live WS capture intentionally paused right now (e.g. cost-control, a planned
migration) or is this a genuine, unnoticed outage? (2) if genuine outage — what's the correct relaunch target (VM
template / launcher script / supervisor) for the live capture process, so a data_engineering dispatch can bring it back
up and verify with a fresh manifest row within the hour, not just believe it's running?

## Todos

- [ ] [DESIGN] P1. Operator/main: confirm intentional-pause vs. genuine outage for CeFi live WS tick capture. (repo:
      unified-trading-pm — decision, routes the next todo)
- [ ] [INFRA] P1. If genuine outage: identify + relaunch the correct live-capture deployment target for CeFi
      (`book_snapshot_5`/`trades`/`depth_of_book_10` etc.), verify a fresh `captured` manifest row lands within the hour
      post-relaunch (not just VM `RUNNING` status — the "no fire-and-forget" HARD RULE). (repo: market-tick-data-service
      / deployment-service)
