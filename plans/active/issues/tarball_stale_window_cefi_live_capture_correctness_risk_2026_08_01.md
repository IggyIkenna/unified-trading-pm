---
doc_type: issue
title: >-
  code-tarball-refresh outage window (2026-07-30T13:02Z→2026-08-01T12:42Z) left MTDS's floating tarball missing several
  "100% empty live capture" bugfixes — credible data-correctness risk, needs manifest-level confirmation
summary: >-
  Todo #3 of `code_tarball_refresh_job_silently_failing_since_2026_07_30_2026_08_01.md` asked to audit whether any VM
  launched under `LC_TARBALL_FRESHNESS=warn` (default) during the code-tarball-refresh outage ran on materially stale
  code. Confirmed: `mtds-code.tar.gz`'s floating manifest was not successfully rebuilt between (at latest)
  `2026-07-30T13:02Z` and `2026-08-01T12:42:24Z` (~47.5h) — during that window,
  `market-tick-data-service@live-defi-rollout` received several commits explicitly described as fixing "100% empty live
  capture" (Binance-Futures/ASTER wire-shape, OKX-FUTURES canonical-id/channel) plus a same-day cefi perp_funding
  manifest-write data-loss regression+revert. Any VM that pulled the floating `mtds-code` tarball in that window (and
  did not separately pin `MTDS_TARBALL_SHA`) ran without these fixes. Confirmed real backfill-fleet VM activity occurred
  inside the window, but the one concrete VM I traced (`cefi-queue-heavy-binancefutu-x17`) turned out to run the Tardis
  HISTORICAL-file backfill path, not the live-WS path the fixes target — so it is likely unaffected by these SPECIFIC
  fixes. I could not, within this audit's scope, locate a production continuous LIVE-capture VM launch inside the window
  to confirm or rule out actual impact — this needs a focused follow-up (manifest capture_status / row-count check for
  the named venues over the window) before it can be closed as either "no impact" or escalated to a confirmed P0
  data-correctness incident.
status: open
nature: issue
asset_group: [cefi]
stage: [live]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [vm-tarball-deployment, data-correctness, cefi, live-capture, audit-followup]
related:
  [
    plans/active/issues/code_tarball_refresh_job_silently_failing_since_2026_07_30_2026_08_01.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
  ]
created: "2026-08-01"
parent_epic: infrastructure_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [code_tarball_refresh_job_silently_failing_since_2026_07_30_2026_08_01-worker]
resolved_by:
locked_by:
context_scope: [/codex/05-infrastructure/vm-tarball-deployment.md]
depends_on: []
---

# code-tarball-refresh stale window — cefi live-capture correctness risk (2026-08-01)

## What I found

Working todo #3 of `code_tarball_refresh_job_silently_failing_since_2026_07_30_2026_08_01.md`: "Audit whether any VM
launched since 2026-07-30T13:02Z under `LC_TARBALL_FRESHNESS=warn` ran on materially stale code for a repo with a real
bugfix shipped in that window."

**Staleness windows established** (each tarball's `.manifest.json` `commit_sha`/`created_at`, checked 2026-08-01):

| repo (tarball)                                                                                                                               | floating tarball `created_at`                                                  | real (non-ci/deps) fix commits since 2026-07-30T13:02Z     |
| -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| `mtds-code`                                                                                                                                  | `2026-08-01T12:42:24Z` (i.e. floating for ~47.5h through the whole outage)     | ~30, several explicitly "100% empty live capture"          |
| `market-data-processing-service-code`                                                                                                        | `2026-07-31T18:17:07Z`                                                         | 8, incl. honest-absence/manifest correctness fixes         |
| `strategy-service-code`                                                                                                                      | `2026-07-30T23:48:55Z`                                                         | 5                                                          |
| `execution-service-code`                                                                                                                     | `2026-07-30T21:05:20Z`                                                         | 5                                                          |
| `ml-service-code`                                                                                                                            | `2026-07-30T21:05:17Z`                                                         | 0                                                          |
| `batch-live-reconciliation-service-code`                                                                                                     | `2026-07-27T01:31:13Z` (stale since BEFORE the outage)                         | 1, perf-only (column projection), not a correctness change |
| `unified-api-contracts-code`, `unified-trading-library-code`, `instruments-service-code`, `deployment-service-code`, `features-service-code` | all rebuilt `2026-08-01T10:00Z`–`12:42Z` (manual rebuilds, per the parent doc) | many, but the manual rebuild closed most of the window     |

**Highest-materiality MTDS commits inside the ~47.5h stale window** (all confirmed ancestors of the current,
finally-rebuilt `mtds-code` tarball SHA `b2a450e87a30`, i.e. they landed on LDR but were NOT reflected in the floating
tarball until `2026-08-01T12:42:24Z`):

- `4f244845` (2026-07-30T17:07:09Z) — "real Binance-Futures depthUpdate wire shape (b/a, not bids/asks) for
  BINANCE-FUTURES + ASTER book_snapshot_5 -- fixes 100% empty live capture"
- `8a6bbc97` (2026-07-30T22:55:39Z) — "OKX-FUTURES @LIN/@INV canonical-id marker + missing derivative_ticker channel --
  fixes 100% empty live capture"
- `fb32fb65` (2026-07-30T16:48:22Z) — revert of a SAME-DAY regression that "silently dropped every
  kalshi_perp/polymarket_perp/hyperliquid manifest write since ~14:12 UTC" (i.e. a ~2.5h internal window,
  `14:12`→`16:48 UTC` same day, where the bug WAS live before its own revert)
- `a1198300` (2026-07-31T05:41:03Z) + `699c563b` (2026-07-31T09:15:32+0100) — cefi perp_funding manifest re-stamp/race
  fixes (KALSHI_PERP/POLYMARKET_PERP canonical venue field)

**VM-launch evidence gathered** (`gs://deployment-scripts-central-element-323112/vm-logs/`, filtered to VM names
embedding `20260730`/`20260731`/`20260801`, ~1050 total launches in that date range fleet-wide):

- `cefi-queue-heavy-binancefutu-x17-20260730-193717` and `-20260801-120637` both launched AFTER the `4f244845`
  Binance-Futures fix landed (17:07:09Z on 07-30), and neither wrote a `TARBALL_PINS.json` at all (no pins recorded for
  ANY repo — fully floating), confirming they pulled whatever `mtds-code` tarball was floating at boot, which per the
  above was pre-fix. **However**, their `LAUNCH_PARAMS.json` shows `launcher: launch-cefi-sharded-backfill.sh`,
  `START_DATE: 2026-02-01`, and `PROGRESS.json` shows `last_completed_date: 2020-04-28` — this is the Tardis
  HISTORICAL-file backfill path (walking backward through history from 2026-02-01), a DIFFERENT code path than the
  live-WebSocket wire-shape parsing the `4f244845`/`8a6bbc97` fixes target. **This VM is likely NOT exposed to those
  specific fixes** — recording this as a negative finding so a follow-up doesn't re-spend time chasing it.
- I could not locate a genuine PRODUCTION continuous live-capture VM launch (as opposed to `mtds-live-smoke-*` VMs,
  which all predate the outage window, `2026-07-26`–`2026-07-28`) inside the `2026-07-30T13:02Z`–`2026-08-01T12:42Z`
  window via VM-name grep. Two possibilities, unresolved: (a) live cefi capture runs via a long-lived process/deployment
  that was NOT relaunched during this window (in which case it's running whatever code it booted with, likely pre-dating
  2026-07-30 entirely — an orthogonal risk, not caused by this specific tarball-refresh outage), or (b) the actual
  live-capture launcher uses a VM-naming convention my grep patterns (`cefi`+`live`, `okx`, `binance`, `aster`,
  `hyperliquid`, `lighter`, `extended`) missed.

## Why it matters

- Two of the unpicked-up fixes are explicitly self-described by their own commit message as "fixes 100% empty live
  capture" for BINANCE-FUTURES/ASTER and OKX-FUTURES — if a live-capture host DID restart/relaunch and pull the floating
  `mtds-code` tarball inside the 47.5h window, it would have captured ZERO rows for those venues the entire time it ran
  on the stale tarball, silently (this is the exact same failure class root-caused in
  `defi_morpho_lending_indices_never_wired_2026_07_12.md`, the incident `lc_verify_tarball_freshness` itself was built
  to catch — but `warn` mode never blocks).
- The `fb32fb65` revert describes ACTUAL, CONFIRMED data loss ("silently dropped every kalshi_perp/polymarket_perp/
  hyperliquid manifest write") during its own ~2.5h introduction-to-revert window on 2026-07-30 — orthogonal to the
  tarball-staleness question (that damage happened regardless of any VM's tarball freshness, since it was live on LDR
  itself), but worth cross-checking manifests for that exact narrower window too.
- Per the data-pipeline-correctness HARD RULE, a credible risk like this cannot be silently closed — it needs a
  manifest-level check, not just code-archaeology, before anyone can say "no impact."

## Todos

- [ ] [DATA] P1. Identify the actual deployment mechanism for continuous live CEFI tick capture (VM vs. long-lived
      service/Pub/Sub-fed process) — confirm whether it restarts/relaunches on any cadence, and if so, whether that
      cadence intersected `2026-07-30T13:02Z`–`2026-08-01T12:42Z`. (repo: market-tick-data-service)
- [ ] [DATA] P1. Check manifest `capture_status`/row-counts for `BINANCE-FUTURES`, `ASTER` (`book_snapshot_5`),
      `OKX-FUTURES` (`derivative_ticker`), and `KALSHI_PERP`/`POLYMARKET_PERP`/`HYPERLIQUID` `perp_funding` for
      `2026-07-30` through `2026-08-01`. A confirmed zero/empty-row stretch for any of these during the relevant
      sub-window is a **confirmed P0 data-correctness incident** — escalate immediately per the HARD RULE (do not
      defer). If no such stretch is found (e.g. the live host never restarted in the window, or was already pinned
      separately), downgrade/close this doc with that evidence cited. (repo: market-tick-data-service)

## Codex SSOTs

`/codex/05-infrastructure/vm-tarball-deployment.md`, `/codex/02-data/data-pipeline-correctness-hard-rule.md`.
