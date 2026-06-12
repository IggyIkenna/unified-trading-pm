---
title: "GitHub Actions BILLING wall — fleet-wide CI outage (every v2 job insta-fails)"
created: 2026-06-11
source:
  - live diagnosis 2026-06-11 ~16:10Z — every quality-gates-v2 job (PM + deployment-api + fleet) fails in ~7s, 0 steps
locked_by: live-defi-rollout
priority: P2
status: active
---

# GitHub Actions billing wall — fleet-wide CI outage

## What I found

From ~2026-06-11T16:10Z every `quality-gates-v2` job fleet-wide fails in ~7 s with **zero steps executed**. Run
annotation (`gh run view 27361472099 --repo IggyIkenna/unified-trading-pm`):

> The job was not started because **recent account payments have failed or your spending limit needs to be increased**.
> Please check the 'Billing & plans' section in your settings

This is GitHub-account billing on `IggyIkenna` — not a workflow/code problem (python-quality-gates-v2.yml unchanged +
actionlint-clean; the same signature reproduces on PM, deployment-api, and dispatch + pull_request triggers alike).
deployment-ui#104 merged minutes earlier on a green v2 — the wall began between those runs.

## Why it matters

**ALL promototion machinery is frozen**: LDR→staging drains, staging→main, semver-agent, SIT, ldr-to-main-promote —
every Actions-backed gate. Armed auto-merge PRs (PM#273, deployment-api#59) sit BLOCKED until Actions runs again.

## Recommended decision

Operator-only (payment instrument): **github.com/settings/billing** → fix the failed payment / raise the Actions
spending limit. No code change needed; on restoration the armed PRs re-run v2 and self-merge. Paged to Slack (#alerts
webhook, direct curl — the notify-slack workflow itself cannot run) + desktop push 2026-06-11.

## Recurrence log

**2026-06-12 ~02:17Z** — billing wall struck again mid-session (escalation agt-35f2b9, slot 1):
- CI succeeded fleet-wide at 01:51Z, then failed starting 02:17Z (window: ~50+ minutes confirmed still failing at 03:12Z)
- Confirmed private-repo pattern: `unified-trading-system-ui` (public repo) CI succeeded throughout; all private repos (MDPS, PM, UTL, UAC, features, strategy, execution, alerting) fail 2-8s with 0 steps
- Local QG for `market-data-processing-service` = GREEN (1867 tests pass); code is correct
- `ldr-to-staging` PR #281 blocked; re-trigger once billing restored: `gh workflow run quality-gates-v2.yml --repo IggyIkenna/market-data-processing-service --ref live-defi-rollout`
- Pattern: payment-failed billing wall — operator action required
