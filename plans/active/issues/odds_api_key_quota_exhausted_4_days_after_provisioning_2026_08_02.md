---
doc_type: issue
title:
  "odds-api-key (The Odds API, 5,000,000-credits/month subscription provisioned 2026-07-29) is ALREADY EXHAUSTED
  (x-requests-remaining: -772) as of 2026-08-02, just 4 days later -- with no live WS VM running to explain the burn"
summary:
  "While verifying sports_live_availability_and_source_latency_2026_07_24.md's open P2 todo (resume the primary odds_api
  live connector), confirmed via direct curl against https://api.the-odds-api.com/v4/sports (using unified-trading-sa's
  Secret Manager access to odds-api-key, 2026-08-02) that the account has burned through its entire
  5,000,000-credit/month allocation and gone NEGATIVE: x-requests-remaining=-772, x-requests-used=5000772. This is the
  SAME key the operator provisioned 2026-07-29 and live-verified at x-requests-remaining=5000000 (per
  sports_live_availability_and_source_latency_2026_07_24.md's P2 todo evidence). Separately confirmed via `gcloud
  compute instances list --project central-element-323112` (2026-08-02) that ZERO mtds-live-sports-* VMs are currently
  running anywhere in the fleet -- so the 60s-interval live WS connector (odds_api_ws.py, the only identified consumer
  with a known per-poll credit cost, ~43k credits/mo estimated) cannot be the source of this burn; something else is
  consuming ~5,000,000 credits in under 4 days (~1.25M/day), a rate roughly 29x the estimated live-polling burn and yet
  the live poller was never running. Candidate consumers not yet investigated: the BATCH odds_api capture path
  (confirmed separately as actively writing real daily data -- see
  sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md's addendum), other slots/sessions/backfill
  scripts hitting the same shared key directly, or a misconfigured retry/polling loop somewhere in the fleet."
status: open
nature: issue
asset_group: [sports]
stage: [data, live]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [odds-api, quota, billing-waste, sports, data-correctness, live-connector]
related:
  [
    /plans/active/sports_live_availability_and_source_latency_2026_07_24.md,
    /plans/active/issues/sports_api_football_live_odds_second_source_conflicts_with_wipe_ruling_2026_08_02.md,
    plans/archive/issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md,
  ]
created: 2026-08-02
parent_epic: sports_master
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: unknown
assigned_vm: planning
execution_scope: orchestrator-agent
source: [infra_capture_and_devops_leftovers-001 backlog task, slot 3, 2026-08-02]
resolved_by:
locked_by:
depends_on: []
last_updated: 2026-08-02
context_scope:
  [
    /plans/active/sports_live_availability_and_source_latency_2026_07_24.md,
    /plans/archive/issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md,
    /plans/active/issues/sports_api_football_live_odds_second_source_conflicts_with_wipe_ruling_2026_08_02.md,
    market-tick-data-service/market_tick_data_service/live/connectors/odds_api_ws.py,
  ]
---

## Why this matters

This is a PAID subscription (operator-provisioned 2026-07-29 specifically to relieve a quota constraint) that has gone
from full (5,000,000) to negative (-772) in under 4 calendar days, while the one KNOWN consumer with a documented credit
cost (the live WS connector) was never running. Either (a) the BATCH capture path is burning far more credits than
expected and needs its own accounting, (b) something is calling this key far more heavily than any tracked pipeline, or
(c) the "5,000,000/month" entitlement itself is not what was believed (e.g. a shorter reset window, or the account is
actually on a smaller tier and the initial 5,000,000 reading was a one-time signup credit, not a recurring monthly
allocation). Left uninvestigated, resuming the live VM per the sibling plan's own "Done when" would launch a producer
against an exhausted/negative-balance key — likely to just 401 or silently produce nothing, wasting the VM's compute
cost for zero data.

## Evidence (measured 2026-08-02, live curl via unified-trading-sa Secret Manager access)

```
GET https://api.the-odds-api.com/v4/sports?apiKey=<odds-api-key>
HTTP/2 200
x-requests-remaining: -772
x-requests-used: 5000772
x-requests-last: 0
```

Compare to the 2026-07-29 provisioning check (per the sibling plan's own recorded evidence):
`x-requests-remaining: 5000000` immediately after rotation.

```
gcloud compute instances list --filter="name~live" --project=central-element-323112
  -> zero mtds-live-sports-* instances (5 unrelated live instances found: mtds-live-cefi-consolidated-*,
     4x prediction-live-kalshi/polymarket-*)
```

## What to check next (not attempted in this pass)

1. Confirm the actual billing/reset terms of this odds-api-key subscription directly with The Odds API dashboard/
   billing page (operator-only access) — is 5,000,000 a recurring monthly figure or a one-time signup credit?
2. Audit every caller of this secret across the fleet (`grep -rn odds-api-key` / `odds_api_secret_name` across
   market-tick-data-service, instruments-service, any backfill/one-off scripts) for polling cadence and whether any are
   looping without the intended interval/backoff.
3. Check the BATCH odds_api capture path's actual call volume for the 2026-07-29..08-02 window (manifest `attempted_at`
   row counts × estimated credits/call) to see if it alone could plausibly explain ~5M credits in 4 days.
4. Once root-caused: either request a quota increase / fix the runaway consumer, THEN resume the live VM per
   `sports_live_availability_and_source_latency_2026_07_24.md`'s P2 todo.

## Progress Log

- **2026-08-02** — Filed by slot 3 (data_engineering) while working `infra_capture_and_devops_leftovers-001` / verifying
  the sibling plan's live-resume todo. Not investigated further in this pass (scope: surface the finding, not root-cause
  it) — no code changed, no VM launched.
- **context-scout 2026-08-03**: populated context_scope (4 entries).
