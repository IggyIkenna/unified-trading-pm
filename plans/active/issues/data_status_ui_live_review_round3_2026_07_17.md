---
doc_type: issue
title:
  Data-status page — live UI review round 3 (2026-07-17 pm) — league names, unknown-error panels, catalogue dropdowns
summary:
  Operator live-reviewed the deployed instruments-service data-status page 2026-07-17 pm and reported four UI findings.
  This doc TRACKS all of them and their fix status. (1) Fixtures browser groups by raw API-Football numeric league_id
  instead of the human canonical league name. (2) New listings + Upcoming expiries + Prediction catalogue panels show
  "Unknown error" — backend code VERIFIED WORKING against real GCS locally, so this is a deploy-lag / client-timeout
  issue, not a code bug. (3) Catalogue Explorer venue / data_type / instrument_type are free-text inputs that should be
  dropdowns of the real distinct values.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, deployment-api, unified-api-contracts]
scope: [engineer]
tags: [data-status, deployment-ui, deployment-api, ux, fixtures, prediction, catalogue, sports]
related: [data_status_page_ux_and_canonicalisation_2026_07_16.md]
created: 2026-07-17
last_updated: 2026-07-17
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
assigned_role: ui_developer
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
source: operator live UI review 2026-07-17 pm (screenshots in chat)
depends_on: []
---

# Data-status page — live UI review round 3 (2026-07-17 pm)

Operator reviewed the deployed instruments-service data-status page and reported four findings. Tracked here per the
operator's "keep adding these to docs to keep track and fix all" instruction. Each row carries its diagnosis + fix
status; updated as they land.

## Findings

### F1 — Fixtures browser: leagues shown as raw API-Football numeric IDs, not human names — `- [ ]` OPEN

The Fixtures browser groups by `league_id` and renders the raw API-Football numeric id as the group header (`103`,
`104`, `113`, `129`, `2`, `253`, …). Operator wants the **human canonical league name** (e.g. 103 → Eliteserien, 2 →
UEFA Champions League). **These league IDs ARE resolvable** — UAC carries
`canonical.domain.sports.league_registry.LEAGUE_REGISTRY` (keyed by canonical league_id) + a reverse
`api_football_id → league_id` map + `get_league(league_id)`. Fix direction: resolve at the **backend**
(`deployment-api/services/fixtures_browser.py` builds the `FixturesByLeagueAndDay` league keys) so the response carries
a human `league_name` alongside the id — league data is UAC data, the UI must not hardcode a mapping. Then the UI
renders the name (id as a subtitle/tooltip). Honest-absence: an id with no registry entry shows the raw id, never a
fabricated name.

### F2 — New listings + Upcoming expiries + Prediction catalogue: "Unknown error" — `- [x]` FIXED (OOM), pending deploy-verify

**CORRECTED diagnosis (2026-07-17 pm): the root cause is a container OOM, NOT deploy-lag/latency and NOT a code-logic
bug.** My first pass said "deploy-lag" — that was wrong; I confirmed it by reading the LIVE Cloud Run logs (ground
truth), not by inference. The service code is correct (all three service functions return data against real GCS:
`list_new_listings(30)` → 440,433 rows, `list_upcoming_expiries(7)` → 6,180 rows, `read_prediction_catalogue(50)` →
total 2,673,118, all OK with the A4 `question` `_READ_COLUMNS` addition). But the DEPLOYED revision (`00195-jr9`,
deployed 17:01, only ~30 min old — so promotion was NOT the issue) logged:

```
Memory limit of 8192 MiB exceeded with 8585 MiB used.  (2026-07-17T17:21:30Z)
… /api/data-status/prediction-catalogue         → 500
… /api/instruments/new-listings                 → 500
… /api/instruments/upcoming-expiries            → 500
… /api/data-status/coverage-summary (×2 svc)    → 500
… /api/capabilities/service-asset-groups        → 500   (all 500 at the SAME 17:21:14 timestamp)
```

The data-status page **mounts several heavy catalogue-reading panels simultaneously** on tab open (New listings +
Upcoming expiries read all five per-AG `prod/catalog.parquet` objects; Prediction catalogue reads the 184 MB / 2.67M-row
prediction catalogue, now 25 cols after this session's `question` backfill — so my A4 work slightly _increased_ the
footprint; coverage-summary / drilldown read the availability index). Under Cloud Run `concurrency=80`, a cold
first-mount burst packs all of them onto ONE 8 GiB instance → 8585 MiB > 8192 → the container is **killed**, taking
every in-flight request with it → the UI renders "Unknown error" on ALL panels at once (exactly the operator's
screenshot). Intermittent (1 OOM / 6h) because a warm 5-min TTL cache hit avoids the cold burst — hence "sometimes
works, sometimes Unknown error". This is the SECOND OOM on this service (the first,
`deployment_ui_data_status_drilldown_oom_and_leaf_schema_2026_07_15`, bumped it 8Gi; the page has grown since).

**Fix SHIPPED — `deployment-api@18a362ec` (`cloudbuild.yaml`): `--memory 8Gi → 16Gi`** (2× over the failing 8585,
matching the dedicated rollup service's 16Gi). Reads are already column-pruned + TTL-cached, so headroom is the right
lever for a cold burst; a code-level fix (an in-container `asyncio.Semaphore` capping concurrent heavy catalogue loads,
modelled on `_deploy_turbo._drilldown_build_semaphore`) is the documented follow-up if it recurs at 16Gi. **Pending:
verify the promoted revision reaches 16Gi + no further OOM against the DEPLOYED endpoint.**

### F3 — Catalogue Explorer: venue / data_type / instrument_type should be dropdowns, not free-text — `- [ ]` OPEN

The Catalogue Explorer's VENUE / INSTRUMENT TYPE / DATA TYPE filters are free-text `optional` inputs. Operator wants
**dropdowns of the real distinct values** for the selected asset_group (typing a venue exactly is error-prone). Fix
direction: a small backend endpoint (or reuse an existing one) returning the distinct venue / instrument_type /
data_type values present in the selected `(service, asset_group)` catalogue — the `_catalogue.py` read already loads the
frame, so distinct-values is cheap and single-walk-safe — then the UI renders `<select>`s populated from it, scoped to
the chosen asset_group, with an "all/any" default. `[UI]` + pw:L2.

## Fix status

| #   | Finding                      | Repo(s)                        | Status                                                               |
| --- | ---------------------------- | ------------------------------ | -------------------------------------------------------------------- |
| F1  | Fixtures league human names  | deployment-api + deployment-ui | OPEN                                                                 |
| F2  | 3 panels "Unknown error"     | deployment-api (`cloudbuild`)  | ✅ FIXED (OOM, not deploy-lag) — mem 8→16Gi @18a362ec; verify deploy |
| F3  | Catalogue Explorer dropdowns | deployment-api + deployment-ui | OPEN                                                                 |
