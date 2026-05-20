---
title: Harsh wake-up handoff 2026-05-20 23:00 UTC
type: handoff
status: active
operator: ikenna (offline ~5h from 23:00 UTC 2026-05-20 — wake check)
audience: harsh
related:
  - ../plans/active/human_work_backlog_2026_05_20.md
  - ../plans/active/data_pipeline_master_coordination_2026_05_20.md
  - ~/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-1/memory/project_orchestrator_overnight_2026_05_20.md
---

# Harsh wake-up handoff — 2026-05-20 23:00 UTC

> Ikenna left at ~22:40 UTC for ~5h. The orchestrator + backlog + slot allocation have been set up so you wake up to (a)
> clear state, (b) ~14 backlog tasks pinned to slot 2 (your interactive slot), (c) 10 adapter scaffolds you can claim by
> bandwidth, (d) the rest of the fleet running centralised work.

## What changed overnight (2026-05-20 22:00-23:00 UTC)

Pushed:

| Change                                                                                                                                                                                                                             | Where                                                                        |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Refresh-usage parser fix (bumped render window 6s → 10s + retry-once on parse failure)                                                                                                                                             | agent-orch@27e7d79                                                           |
| Kicker scrollback widened to 500 lines for context% extraction on actively-working slots                                                                                                                                           | agent-orch@4436771                                                           |
| Account-failover triggers codified (weekly + sonnet + 5h + rate_limited_until, all four conditions)                                                                                                                                | agent-orch@e7c78d3 in agents/main.md                                         |
| Human-work backlog r2 — 14 new items (6 Ikenna + 8 Harsh) for post-May-23 parallel-prep tracks (paper-trade DeFi audit, archetype mechanics for CeFi/TradFi/Sports/Prediction, batch ML/strategy/exec wiring, paper-trade harness) | PM@ff62c2137 in plans/active/human_work_backlog_2026_05_20.md                |
| Coordinator supervision-layer preamble (Phase 7 split 7a Harsh / 7b Ikenna; Phase 14 joint Ikenna-design / Harsh-exec)                                                                                                             | PM@b62330b86 in plans/active/data_pipeline_master_coordination_2026_05_20.md |
| 36 new backlog.yaml entries (HUMAN-HARSH-_ + HUMAN-IKENNA-_ + ADAPTER-\*) reloaded into orchestrator                                                                                                                               | PM@c19ecebbc + /api/backlog/reload                                           |
| 24 archived ml-\* worktrees removed from VM (.tabs/<N>/{ml-inference-service,ml-training-service})                                                                                                                                 | reconcile-archived-worktrees.sh --apply                                      |
| Slots 13-20 provisioned on VM (.tabs/13-20/<repos>)                                                                                                                                                                                | setup-tab-worktrees.sh --add-slot                                            |
| Slot 2 paused for your interactive session                                                                                                                                                                                         | POST /api/slots/2/pause                                                      |
| Slots 5 + 10 respawned with ikenna-backup creds (were 401 auth-broken from acct swap)                                                                                                                                              | POST /api/slots/{5,10}/spawn                                                 |
| Slots 6 + 9 + 11 nudged with /boot directives (were frozen with text-in-buffer from prior session)                                                                                                                                 | tmux send-keys                                                               |
| /boot-per-unit HARD RULE broadcast to all working slots via /api/slots/N/message                                                                                                                                                   | server message queue                                                         |

## Slot allocation (operator r2 confirmed)

| Slot  | Host                   | Operator                   | Status (23:00 UTC)                | Work                                                       |
| ----- | ---------------------- | -------------------------- | --------------------------------- | ---------------------------------------------------------- |
| 1     | Ikenna mac             | Ikenna interactive         | paused                            | Operator's interactive slot (paused while away)            |
| **2** | **Your local pc / VM** | **You interactive**        | **paused — attach when you wake** | **Your interactive slot — see HUMAN-HARSH-\* queue below** |
| 3-11  | VM                     | Centralised Sonnet workers | mostly working                    | Centralised work + your QG/CI/CD/AWS tasks as they pick up |
| 12-20 | VM (worktrees only)    | —                          | provisioned, no worker            | Spawn workers as needed via dashboard "Spawn" button       |

## Your queue (target_slot=2, tier=1 — ready to pick up immediately)

1. **HUMAN-HARSH-WORKSPACE-QG-CLUSTER-A** (UAC + UTL + IS) — `bash scripts/quality-gates.sh` exit 0 across all 3 repos,
   surface-only fixes
2. **HUMAN-HARSH-WORKSPACE-QG-CLUSTER-B** (MTDS + features + MDPS) — same. **Note**: features-service likely needs
   `PYTEST_UNIT_DIR="tests/"` override per CLAUDE.md
3. **HUMAN-HARSH-WORKSPACE-QG-CLUSTER-C** (strategy + execution + ml) — surface-only under STRATEGY-LOGIC freeze gate.
   Do NOT modify strategy_service/engine/strategies/v2/, engine/allocator/, collateral/, liquidation/,
   cross-venue-transfer/. If a QG fix needs logic touch → BLOCKED + ping
4. **HUMAN-HARSH-CI-CD-PROMOTION-TEST** — drive a full LDR → staging → SIT → main cycle on a non-critical service
   (alerting-service or a util package). Validate workflow before May-23 cutover
5. **HUMAN-HARSH-AWS-MANIFEST-CONSOLIDATOR-SCOPING** — AWS-side consolidator port scoping (currently only GCP has the
   Cloud Run jobs). Output: sub-plan filed OR `BLOCKED-OPERATOR-DECISION` ping
6. **HUMAN-HARSH-LAPTOP-MIGRATION** — complete codex/12-agent-workflow/harsh-laptop-migration-2026-05-20.md Steps 1-8

## Your gated queue (tier=50 — runs once phase-\* conditions flip)

- HUMAN-HARSH-BATCH-ML-{CEFI, TRADFI, SPORTS, PREDICTION} — gated on `phase-11-operational-backfill-green`
- HUMAN-HARSH-BATCH-STRATEGY-EXEC-{CEFI, TRADFI, SPORTS-PREDICTION} — gated on Harsh ML done +
  `phase-14-strategy-topology-green`
- HUMAN-HARSH-PAPER-TRADE-HARNESS-CROSS-ASSETGROUP — gated on Harsh strategy/exec done
- HUMAN-HARSH-PHASE-5/6/7A/9/11 (the data-pipeline coordinator phases pinned to you) — gated on upstream phase greens

## Adapter scaffolding (bandwidth-claimed — any slot, including yours)

10 BLOCKED-CREDENTIALS adapters with scaffolds + unit tests + UAC contracts ready to ship. Integration tests stay
`@pytest.mark.requires_credentials` until Ikenna files the credential ask. Pick whichever has bandwidth:

- ADAPTER-HELIUS-SOLANA-PAID (slot 8 just took this)
- ADAPTER-GLASSNODE-ONCHAIN
- ADAPTER-KAIKO-CEX-HISTORICAL
- ADAPTER-POLYGON-IO-TRADFI-TICKS
- ADAPTER-DATABENTO-TRADFI
- ADAPTER-SPORTRADAR-FEED
- ADAPTER-FOOTYSTATS-FEED
- ADAPTER-THE-ODDS-API
- ADAPTER-POLYMARKET-FEED
- ADAPTER-KALSHI-FEED

Each = ~0.3-0.5 cal-AI-day. Whoever takes one ships:

- UAC contract (schema + endpoints from vendor public docs)
- Auth shape (header / OAuth / API key)
- Retry/backoff/rate-limit semantics
- Error classifier via `classify_venue_error()` + `ADAPTER_FETCH_FAILED` emission
- Manifest emission per writegate Phase 6.x
- Unit tests against mocked API responses
- Integration tests marked `@pytest.mark.requires_credentials`
- File CREDENTIAL APPROVAL REQUEST in pings/slot_1.md per CLAUDE.md `External Data Is Always Available` format

## Coordinator-phase ↔ owner cross-reference

For data_pipeline_master_coordination_2026_05_20.md phases:

| Phase                                         | Owner                                                            | Status                                                        |
| --------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------- |
| -2 Bucket 4 archetype audit                   | Ikenna                                                           | in-progress (operator session)                                |
| -1 Workspace QG green                         | **Harsh — your QG cluster A/B/C tasks**                          | queued                                                        |
| 1 AWS-GCP bucket symmetry                     | VM slots 2+3 / 8                                                 | DONE                                                          |
| 5 AWS bucket migration                        | Harsh (your PHASE-5\* tasks)                                     | gated on phase-3-vm-drain-green + phase-4-gcs-migration-green |
| 6 Docker rebuild + VM redeploy                | Harsh                                                            | gated on phase-5-aws-migration-green                          |
| 7a Schema migration (mechanical v<8 → v8)     | Harsh                                                            | gated on phase-6-docker-rebuild-green                         |
| 7b DIVERGENT_EMPTY triage (per-cell judgment) | **Ikenna**                                                       | gated after 7a                                                |
| 9 Deployment-UI denominator/numerator         | Harsh                                                            | gated on phase-8-unfreeze-active                              |
| 11 Operational data backfill                  | Harsh                                                            | gated on phase-10-qg-enforcement-green                        |
| 12 Live adapter completion                    | **Co-owned** (creds=Ikenna / scaffolds=bandwidth / wiring=Harsh) | active (adapter scaffolds queued)                             |
| 13 Batch-live symmetry                        | Harsh                                                            | gated on phase-12                                             |
| 14 Topology cleanup                           | **Ikenna design / Harsh execute**                                | gated on phase-13                                             |

Supervision cadence: operator decides per-phase as it lands (no fixed cadence). Both sides maintain phase-of-record
updates in their own `_agent_pings.md` as phases land GREEN. **Plan reviewer rejects phase-flip commits in
`data_pipeline_master_coordination` that don't reference an LDR commit-sha + brief evidence line.**

## Current account state

| Account                              | Status    | Weekly | 5-hour | Sonnet (weekly) |
| ------------------------------------ | --------- | ------ | ------ | --------------- |
| harsh-primary                        | available | 74%    | 51%    | 76%             |
| **ikenna-backup** (currently active) | available | 1%     | 4%     | 0%              |

ikenna-backup has ~30× more headroom on weekly. Stay on it unless any of the 4 failover conditions trigger (see
agents/main.md § "Account-failover triggers").

## How to wake up + pick up work

```bash
# 1. SSH into the VM (you have access)
ssh agent-orchestrator-vm

# 2. Attach to your interactive slot 2
tmux attach -t orch-slot-2

# (or if slot 2 has stale claude session: kill it + spawn fresh)
# tmux kill-session -t orch-slot-2
# curl -X POST https://api.agent-orchestrator.odum-research.com/api/slots/2/spawn \
#   -H "Authorization: Bearer $(cat ~/.orch_token)" \
#   -d '{"account_id":"harsh-primary","boot_prompt":"...","cwd":"/home/ubuntu/unified-trading-system-repos/.tabs/2","model":"opus","effort":"max"}'

# 3. Resume slot 2 in orchestrator so dispatcher knows you're active
curl -X POST https://api.agent-orchestrator.odum-research.com/api/slots/2/resume \
  -H "Authorization: Bearer $(cat ~/.orch_token)"

# 4. Pull your next task
curl -X POST https://api.agent-orchestrator.odum-research.com/api/slots/2/boot \
  -H "Authorization: Bearer $(cat ~/.orch_token)"

# You'll get the highest-priority HUMAN-HARSH-* task targeting slot 2.
# Start with QG-CLUSTER-A (lowest priority number = first in queue).
```

If you'd rather just look at the dashboard, https://agent-orchestrator.odum-research.com/ shows the Backlog panel with
your queue + the slot 2 card.

## Heads-up — known issues

1. **agent-orchestrator branch on .tabs/{14,16,18,20}** — `tab/ikennaigboakam/<N>` already exists, so the bootstrap
   script skipped agent-orchestrator for those slots. Other repos are present. If you spawn workers in those slots and
   they need agent-orchestrator, manually clone via `git worktree add` (one-time fix).
2. **Slot 4 + 7 at high context (99% / 100%)** — they'll compact when they run their next tool call. Watch the dashboard
   for "thrashing" indicator (>3 compactions/hour means a slot's stuck in a loop).
3. **Main agent `agt-7eb095`** — registered as active but `last_seen_at` is null. May or may not be alive. I didn't
   restart it (operator said don't kill). If you need to verify: `tmux attach -t orch-agent-main-7eb095` on VM.
4. **No mass-spawn of slots 12-20** — worktrees provisioned but no claude sessions started. Spawn on demand via
   dashboard. The pre-spawn dirty-state gate is in REFUSE mode by default — use `dirty_state_resolution: stash` in the
   spawn body if a slot has untracked files from previous setup.

## Operator-pending items (NOT for you — Ikenna picks up when back)

- HUMAN-IKENNA-ARCHETYPE-AUDIT (in-progress; D1-D14)
- HUMAN-IKENNA-DATA-PIPELINE-COORDINATION (Phase 7b triage + Phase 14 design)
- HUMAN-IKENNA-CROSS-CLIENT-ISOLATION-AUDIT
- HUMAN-IKENNA-PROMOTE-WORKFLOW-REVIEW
- HUMAN-IKENNA-CREDENTIALS-UNBLOCK-TRACK (filings for 10 adapters)
- HUMAN-IKENNA-CUSTODY-PROVIDER-DECISIONS (Copper + CEFFU)
- HUMAN-IKENNA-PAPER-TRADE-DEFI-AUDIT (3-trading-day window post-cutover)
- HUMAN-IKENNA-{CEFI, TRADFI, SPORTS, PREDICTION}-ARCHETYPE-DESIGN (gated on archetype audit done)
- HUMAN-IKENNA-PAPER-TRADE-AUDIT-CROSS-ASSETGROUP (gated on your harness done)

## Composes with

- `plans/active/human_work_backlog_2026_05_20.md` — full split principles + sequencing
- `plans/active/data_pipeline_master_coordination_2026_05_20.md` — phase ordering DAG
- `agent-orchestrator/agents/worker.md` — /boot-per-shippable-unit HARD RULE
- `cursor-configs/CLAUDE.md` § "Commit + Push + Flip Plan Checkboxes As You Ship Each Item" — same-turn Half-1 +
  Half-2 + Half-3
