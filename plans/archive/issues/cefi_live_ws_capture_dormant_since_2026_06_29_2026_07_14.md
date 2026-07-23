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
status: resolved
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [live-capture, data-correctness, big-finding, orderbook]
related: [/plans/active/l2_book_microstructure_capture_2026_07_13.md]
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
resolved_by: "operator/main via BLK-55d45a68 (2026-07-14) — intentional pause confirmed, not a genuine outage"
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

## Investigation update — 2026-07-14 (slot 3, todo 1 research)

Dispatched to confirm intentional-pause vs. genuine-outage. Read-only git-history + doc grep across
`market-tick-data-service`, `deployment-service`, `unified-trading-pm` (no VM relaunch attempted — that stays gated on
operator confirmation per the recommendation above):

- **No evidence of a deliberate pause/kill-switch.** No commit, terraform change, or plan doc turns CeFi live capture
  off as an intentional decision. `/codex/04-architecture/autonomous-recovery-matrix.md`'s kill-switch machinery is
  scoped to trading/execution risk, not data-capture — unrelated.
- **Strong circumstantial evidence of a stalled infra migration around 2026-06-27–29, not a clean outage:**
  - `deployment-service/scripts/vm/launch-mtds-live-cefi-consolidated.sh` (header dated 2026-06-27) redesigns CeFi live
    capture from 16 VMs/shard (~$103/day) to one consolidated `e2-highmem-16` (~$17/day) — a genuine cost-control
    rearchitecture landing right before the dormancy window.
  - `market-tick-data-service` swapped the live tick sink twice in 3 days: `3043f2dc` (2026-06-26) reverted to
    direct-GCS writes after finding the Pub/Sub `LiveEventFacadeSink` silently dropped data (`InMemoryTransport` bug);
    `1e583b90` (2026-06-28) switched back to `LiveEventFacadeSink`; `7fae3c0b`/`78fc436f` (2026-06-29 05:24) made
    `PubSubTransport` the active default again.
  - `deployment-service@e87abb1` (2026-06-29 06:02): IAM fix ("use unified-trading-sa for prediction VM to unblock
    pubsub publish") landing the same morning.
  - `deployment-service@c540cd0`: "apply live_event_log warm-sink — 52 Cloud Storage subscriptions created" (terraform).
  - The sibling **prediction** asset-group's consolidated live VM WAS successfully relaunched that same day
    (`mtds-live-prediction-consolidated-20260629-060558`, per
    `plans/active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md:2277`) — proving the team was actively
    re-standing-up consolidated live VMs asset-group-by-asset-group on 2026-06-29. **No equivalent CeFi VM
    launch/verification record exists after that date.**
- **Conclusion (medium-high confidence): genuine, unnoticed outage** born from an incomplete migration — the CeFi leg of
  the cost-control consolidation + Pub/Sub cutover appears to have stalled or the VM died post-launch, and attention
  moved to the hundreds of subsequent unrelated commits without anyone confirming CeFi's new live VM ever landed rows.
  Not a smoking-gun "we paused this" doc — timing correlation is strong but not a direct confirmation.
- **Relaunch targets identified for todo 2** (not yet executed): primary =
  `deployment-service/scripts/vm/launch-mtds-live-cefi-consolidated.sh` (+ its startup script
  `setup-cefi-live-consolidated-vm.sh`); legacy per-shard fallback =
  `launch-mtds-live.sh --asset-group cefi --shard-spec ...`; working sibling pattern =
  `launch-mtds-live-prediction-consolidated.sh`.

Escalated to operator via `/blocked` (slot 3) for the intentional-pause vs. outage confirmation before todo 2 executes
any relaunch.

## Resolution (2026-07-14, BLK-55d45a68)

**Operator/main confirmed: INTENTIONAL PAUSE** — cost-control freeze / planned migration still in flight (the
VM-consolidation redesign + Pub/Sub live-sink cutover documented in the investigation update above). This is NOT a
genuine outage; no relaunch is being dispatched. Noted in `/codex/02-data/honest-absence-downstream-handling.md` §
"Reference incidents" so a future audit doesn't re-raise this as a fresh alarm before the migration completes and a live
row lands again.

## Todos

- [x] [DESIGN] P1. Operator/main: confirm intentional-pause vs. genuine outage for CeFi live WS tick capture. (repo:
      unified-trading-pm — decision, routes the next todo) — ✅ RESOLVED 2026-07-14: intentional pause (BLK-55d45a68)
- [x] [INFRA] P1. If genuine outage: identify + relaunch the correct live-capture deployment target for CeFi
      (`book_snapshot_5`/`trades`/`depth_of_book_10` etc.), verify a fresh `captured` manifest row lands within the hour
      post-relaunch (not just VM `RUNNING` status — the "no fire-and-forget" HARD RULE). (repo: market-tick-data-service
      / deployment-service) — ✅ N/A 2026-07-14: confirmed intentional pause, not a genuine outage — no relaunch
      executed.
