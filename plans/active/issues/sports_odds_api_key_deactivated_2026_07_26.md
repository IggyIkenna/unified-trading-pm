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
- [ ] [DATA] P2. **PREREQUISITE UPDATED (see new P1 todo below) — do NOT re-run blind.** Once the key is fixed, re-run
      the 3-league golden-window backfill using the now-shipped `--league` flag:
      `bash deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh --vm-name     mtds-backfill-odds-ucl-gap --league UCL,CHINA_SUPER_LEAGUE,RUSSIA_PREMIER_LEAGUE --start 2025-09-01 --end     2025-11-30 --force`.
      Verify `_index/availability_index.parquet` shows 0 `attempted_failed` for these 3 leagues across the golden window
      afterward (baseline before this fix: only 11/91 days per league captured, all via non-`--league`-scoped organic
      data; 0 `attempted_failed` anywhere for these leagues, confirming no prior code path had ever actually attempted
      the missing ~80 days). **Correction 2026-07-26**: my own run's per-VM shard
      (`gs://instruments-store-sports-prd-central-element-323112/_index/per_vm/mtds-backfill-odds-ucl-gap2.parquet`)
      shows the VM actually fetched 33 DEFAULT Prediction-tier leagues (EPL/LA_LIGA/BUNDESLIGA/MLS/etc.) — NOT the 3
      requested leagues at all, despite `VM_LEAGUE` metadata being correctly set on the instance (verified via
      `gcloud compute instances describe`). The 401s masked this: every league failed identically so the wrong scope
      wasn't visually obvious in the log. This means `--league` may not actually be reaching `_candidate_leagues()`
      end-to-end — see the new P1 todo. Do not re-run at scale until that's root-caused; the fix might not be "just
      re-run" after the credential is fixed. (repo: market-tick-data-service / deployment-service, no code yet —
      operational re-run blocked on the scoping bug too)
- [x] ✅ [DATA] P1. **DONE 2026-07-26 (slot 4)** — Confirmed via direct manifest query
      (`gs://market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet`): ZERO `odds_api`
      rows of ANY `capture_status` (captured or `attempted_failed`) are dated OR written 2026-07-26 in the consolidated
      index, across ALL leagues — vs 275,136 `captured` rows written 2026-07-25. Could not find a dedicated scheduled
      forward-poll launcher for sports odds-api specifically (unlike backfill, which has
      `launch-mtds-sports-odds-backfill-vm.sh`) to confirm whether one has even run today yet. Since the key is
      deactivated at the ACCOUNT level (not per-request/per-VM), this is a logical certainty rather than something that
      needs re-confirming per-job: ANY odds-api call today or any day will 401 identically until the operator fixes it —
      confirmed directly via `curl https://api.the-odds-api.com/v4/sports?apiKey=...` returning `DEACTIVATED_KEY` (see
      above). **Could NOT confirm whether the `attempted_failed` Slack alert fired** — no Slack access from this
      session; that half of the todo needs an operator/dashboard check, not a worker one.
- [ ] [DATA] P1. **NEW 2026-07-26 (slot 4)** — Root-cause why `--league` scoping doesn't reach the odds-api adapter's
      league loop end-to-end. `VM_LEAGUE` metadata IS set correctly on the instance (confirmed via
      `gcloud compute instances describe mtds-backfill-odds-ucl-gap2 ... --format="value(metadata.items)"` →
      `VM_LEAGUE=UCL;CHINA_SUPER_LEAGUE;RUSSIA_PREMIER_LEAGUE`), and `setup-data-pipeline-vm.sh` (deployed tarball,
      confirmed same commit) correctly reads it and appends `--league UCL,CHINA_SUPER_LEAGUE,RUSSIA_PREMIER_LEAGUE` to
      the CLI invocation. `tick_data_handler.py`'s `_resolve_filter_args` (same deployed commit, `47b19985e84e`) also
      correctly reads `args.league` and splits it. Yet the VM's own per-VM manifest shard shows it fetched the DEFAULT
      33-league Prediction-tier pool (`_candidate_leagues()`'s `leagues=None` branch), not the 3 requested leagues —
      meaning the parsed `--league` value never reached
      `_fetch_all_leagues(date_str, leagues)`/`_candidate_leagues(registry, leagues)` somewhere between CLI parsing and
      the adapter call. Needs tracing through `process_ticks()` → `venue_fetch.py` →
      `OddsApiAdapter.download_batch(leagues=...)` to find where the value is dropped (or possibly the deployed
      tarball's actual bytes don't match its claimed manifest sha — worth diffing the live tarball content against
      `git show 47b19985e84e` directly as a sanity check before assuming it's a code bug). This blocks todo P2 above
      from being a simple "re-run once the key works". (repo: market-tick-data-service)

## Progress Log

- 2026-07-26 (slot 4): Found + reproduced the DEACTIVATED_KEY 401 while executing
  `sports_satellite_ao_dispatch_batch5-014`. Stopped the backfill VM, confirmed blast radius via manifest query (275,136
  rows captured 2026-07-25, zero 2026-07-26), filed this doc. The `--league` launcher capability
  (`deployment-service@281426e7`) is real, shipped, tested work — independent of this credential blocker; only the
  actual data-fetch step is blocked. Returning `sports_satellite_ao_dispatch_batch5-014`'s checkbox unchecked with a
  `BLOCKED-CREDENTIALS` annotation pointing here, per the credential-defer carve-out.
- 2026-07-26 (slot 4): Picked up the auto-derived P1 follow-up todo (confirm forward-job blast radius). Confirmed zero
  odds_api activity of any kind dated/written 2026-07-26 in the consolidated manifest. While investigating the per-VM
  shard for evidence, discovered my OWN backfill run never actually respected `--league` — it silently fetched the
  33-league Prediction-tier default instead of the 3 requested leagues, a SEPARATE bug from the credential outage that
  the 401s had masked (every league failed identically, so the wrong scope wasn't visible in the log). Corrected todo P2
  above to not blindly re-run once the key is fixed, and added a new P1 todo to root-cause the scoping gap. This walks
  back my earlier (incorrect) claim in this doc + in `sports_satellite_ao_dispatch_batch5_2026_07_26.md` that the
  `--league` capability was "already shipped and tested" — it is shipped (the metadata/CLI-arg plumbing is real and
  independently useful) but NOT yet proven to actually scope the fetch; that needs the new root-cause todo before it can
  be trusted.
