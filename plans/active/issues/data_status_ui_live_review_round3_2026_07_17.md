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

### F2 — New listings + Upcoming expiries + Prediction catalogue: "Unknown error" — `- [ ]` OPEN (deploy/latency, not a code bug)

All three panels render a red "Unknown error" alongside their empty-state text. **Root cause is NOT a code bug** —
verified 2026-07-17 against real prod GCS in the current LDR checkout:

- `list_new_listings(max_age_days=30)` → **440,433 rows OK**
- `list_upcoming_expiries(within_days=7)` → **6,180 rows OK**
- `read_prediction_catalogue(limit=50)` → **total=2,673,118 OK** (works WITH the A4 `question` `_READ_COLUMNS` addition
  — schema-aware, so the not-yet-present column degrades gracefully; A4 did not break it). So the three endpoints' code
  is correct. The live "Unknown error" is a **client-side fetch failure**, almost certainly a **timeout on a slow cold
  read against a DEPLOYED backend that predates this session's A5 perf fix** — measured: `/prediction-catalogue` cold =
  ~157s (deployment-api@0e39a53 collapses the per-page re-pay to ~0s, but only once deployed);
  `list_new_listings`/`list_upcoming_expiries` read all five per-AG `prod/catalog.parquet` objects (tradfi 1.17M rows /
  prediction 184 MB) so are also multi-second cold. If the browser/gateway timeout is < the cold read, the UI shows
  "Unknown error". **Fix = confirm deployment-api is promoted+deployed at ≥@0e39a53** (see the promotion-lag issue
  `promotion_lag_alert_hides_provenance_block_2026_07_17.md` — MTDS + deployment-ui were sitting un-promoted; check
  deployment-api too). Secondary hardening (if the cold read still exceeds the client timeout even paginated): the
  new-listings/upcoming-expiries reads are per-AG shard-isolated + TTL-cached but pay a cold multi-AG cost; consider a
  warm-on-boot or a narrower default. Verify against the DEPLOYED endpoint, not local.

### F3 — Catalogue Explorer: venue / data_type / instrument_type should be dropdowns, not free-text — `- [ ]` OPEN

The Catalogue Explorer's VENUE / INSTRUMENT TYPE / DATA TYPE filters are free-text `optional` inputs. Operator wants
**dropdowns of the real distinct values** for the selected asset_group (typing a venue exactly is error-prone). Fix
direction: a small backend endpoint (or reuse an existing one) returning the distinct venue / instrument_type /
data_type values present in the selected `(service, asset_group)` catalogue — the `_catalogue.py` read already loads the
frame, so distinct-values is cheap and single-walk-safe — then the UI renders `<select>`s populated from it, scoped to
the chosen asset_group, with an "all/any" default. `[UI]` + pw:L2.

## Fix status

| #   | Finding                      | Repo(s)                                            | Status                             |
| --- | ---------------------------- | -------------------------------------------------- | ---------------------------------- |
| F1  | Fixtures league human names  | deployment-api + deployment-ui                     | OPEN                               |
| F2  | 3 panels "Unknown error"     | (deploy/promote — verify deployment-api ≥@0e39a53) | OPEN — likely deploy-lag, not code |
| F3  | Catalogue Explorer dropdowns | deployment-api + deployment-ui                     | OPEN                               |
