---
doc_type: issue
title:
  "odds-api key DEACTIVATED (failed payment/cancelation) — blocks ALL sports odds-api capture, not just one league
  backfill"
summary: >-
  Investigating sports_satellite_ao_dispatch_batch5-014 (backfill the 3 odds-api league gaps —
  UCL/CHINA_SUPER_LEAGUE/RUSSIA_PREMIER_LEAGUE) found every request to the-odds-api.com returning HTTP 401
  `error_code=DEACTIVATED_KEY` ("This could be due to cancelation or a failed payment"). Confirmed by a direct curl
  against the live API with the exact key MTDS resolves from Secret Manager (`odds-api-key`). The manifest shows 275,136
  `odds_api`-source rows captured successfully on 2026-07-25, and ZERO since — the key was working yesterday and is
  deactivated as of today. This blocks EVERY odds-api sports capture (forward-poll AND backfill), not just the 3-league
  gap this task was scoped to.
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [sports, odds-api, credentials, outage, data-pipeline-correctness, blocked-credentials]
related: [sports_satellite_ao_dispatch_batch5_2026_07_26, sports_golden_window_attempted_failed_remediation_2026_06_24]
created: 2026-07-26
parent_epic: sports_master
assigned_vm: planning
source: [sports_satellite_ao_dispatch_batch5-014]
execution_scope: orchestrator-agent
priority: P0
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# odds-api key deactivated — blocks all sports odds-api capture

## What I found

Dispatched task `sports_satellite_ao_dispatch_batch5-014` ("Backfill the 3 odds-api league gaps surfaced by the
api_football wipe — `soccer_uefa_champs_league`, `soccer_china_superleague`, `soccer_russia_premier_league`, 2025-H2
golden window"). Shipped a genuine prerequisite fix (`deployment-service@281426e7` — added `--league` scoping to
`launch-mtds-sports-odds-backfill-vm.sh`, wiring the already-built `VM_LEAGUE` metadata support in
`setup-data-pipeline-vm.sh` through to a CLI flag), then launched a scoped SPOT VM (`mtds-backfill-odds-ucl-gap2`,
`--league UCL,CHINA_SUPER_LEAGUE,RUSSIA_PREMIER_LEAGUE --start 2025-09-01 --end 2025-11-30 --force`) to actually run the
backfill.

Every single request failed:

```
2026-07-26 07:55:14,267 WARNING Discovery call for soccer_uefa_champs_league on 2025-09-13 FAILED (re-raising):
401, message='Unauthorized', url='https://api.the-odds-api.com/v4/historical/sports/soccer_uefa_champs_league/
odds?apiKey=<REDACTED-DEACTIVATED-KEY>&bookmakers=...'
2026-07-26 07:55:14,267 ERROR Venue ODDS_API: unexpected error (shard isolated): 401, message='Unauthorized', ...
```

Confirmed by direct reproduction against the live API (same key MTDS resolved from the `odds-api-key` Secret Manager
secret):

```
$ curl -sS "https://api.the-odds-api.com/v4/sports?apiKey=<REDACTED-DEACTIVATED-KEY>"
{"message":"API key is deactivated. This could be due to cancelation or a failed payment",
 "error_code":"DEACTIVATED_KEY", ...}
```

This is NOT an honest-absence / no-data condition — it is a genuine upstream credential failure, correctly classified by
the adapter as `record_failed` (shard-level failure isolation held: the VM correctly wrote `attempted_failed` rows per
date instead of silently swallowing the error or mis-stamping `empty_confirmed`).

**Blast radius — this is bigger than the 3-league task it was found under.** Queried the manifest directly:

```
odds_api rows written since 2026-07-24: 275,136 (all capture_status=captured)
  2026-07-25: 275,136 captured
  2026-07-26: 0
```

The key was fully functional yesterday (275k rows captured across the whole sports odds-api surface) and is deactivated
as of today. Every scheduled forward-poll / daily odds-api capture job for sports TODAY is very likely failing with the
same 401, silently unless the `attempted_failed` Slack alert (`deployment-service@cb330f7`, per
`sports_golden_window_attempted_failed_remediation_2026_06_24.md` fix #4) correctly fires on it.

I stopped the backfill VM (`mtds-backfill-odds-ucl-gap2`, `gcloud compute instances stop`) immediately after confirming
the 401 pattern — every further request would just burn compute writing `attempted_failed` rows with zero chance of
succeeding until the key is fixed. No data was lost (idempotent, shard-isolated failure recording only).

## Why it matters

odds-api is the canonical sports bookmaker-odds source (`batch_odds_api`) — this is not a secondary/optional feed. A
deactivated key means the ENTIRE sports odds pipeline (not just the 3-league gap) is currently unable to capture any new
odds data, forward or historical, until the subscription/key is fixed. Per
`/codex/02-data/data-pipeline-correctness-hard-rule.md` and `/codex/02-data/external-data-always-available-rule.md`:
exhausting a paid credential path is a credential ask, not a descope — this needs an operator to actually fix the
odds-api account/billing and rotate the Secret Manager `odds-api-key` value, not a code change.

## Recommended decision

- **Operator action required (cannot be done by a worker)**: check the-odds-api.com account billing/subscription status,
  resolve the cancelation/failed-payment, generate a fresh API key if needed, and update the `odds-api-key` secret in
  GCP Secret Manager (project `central-element-323112`).
- Once fixed, re-run `sports_satellite_ao_dispatch_batch5-014`'s underlying backfill (the `--league` capability is
  already shipped and tested — see Follow-up todo below) — no further code work needed for that task, just a clean
  re-launch once the key works.
- Consider whether the daily/forward sports odds-api job needs a manual catch-up run for 2026-07-26 once fixed (today's
  window will otherwise show a real, if brief, gap).

## Follow-up todos

- [ ] [OPERATOR] P0. Fix the-odds-api.com account billing/subscription (deactivated — cancelation or failed payment) and
      rotate the `odds-api-key` secret in GCP Secret Manager (project `central-element-323112`) to a working key.
      BLOCKED-OPERATOR-DECISION / credential fix — no worker action possible. (repo: N/A, GCP Secret Manager +
      the-odds-api.com account)
- [ ] [DATA] P2. Once the key is fixed, re-run the 3-league golden-window backfill using the now-shipped `--league`
      flag:
      `bash deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh --vm-name     mtds-backfill-odds-ucl-gap --league UCL,CHINA_SUPER_LEAGUE,RUSSIA_PREMIER_LEAGUE --start 2025-09-01 --end     2025-11-30 --force`.
      Verify `_index/availability_index.parquet` shows 0 `attempted_failed` for these 3 leagues across the golden window
      afterward (baseline before this fix: only 11/91 days per league captured, all via non-`--league`-scoped organic
      data; 0 `attempted_failed` anywhere for these leagues, confirming no prior code path had ever actually attempted
      the missing ~80 days). (repo: market-tick-data-service / deployment-service, no code — operational re-run)
- [ ] [DATA] P1. Confirm whether the 2026-07-26 daily/forward sports odds-api job also hit this outage (check
      `_index/availability_index.parquet` for `source=odds_api` `attempted_failed` rows dated 2026-07-26 across ALL
      leagues, not just the 3 in this doc) and whether the `attempted_failed` Slack alert (`deployment-service@cb330f7`)
      actually fired — if it didn't, that's a second, separate finding. (repo: market-tick-data-service)

## Progress Log

- 2026-07-26 (slot 4): Found + reproduced the DEACTIVATED_KEY 401 while executing
  `sports_satellite_ao_dispatch_batch5-014`. Stopped the backfill VM, confirmed blast radius via manifest query (275,136
  rows captured 2026-07-25, zero 2026-07-26), filed this doc. The `--league` launcher capability
  (`deployment-service@281426e7`) is real, shipped, tested work — independent of this credential blocker; only the
  actual data-fetch step is blocked. Returning `sports_satellite_ao_dispatch_batch5-014`'s checkbox unchecked with a
  `BLOCKED-CREDENTIALS` annotation pointing here, per the credential-defer carve-out.
