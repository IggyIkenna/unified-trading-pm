---
doc_type: plan
title: Sports fixtures browser — switch to the single-file catalogue source (P10-B backend + follow-ups)
summary: >-
  Forked from data_status_page_ux_and_canonicalisation_2026_07_16.md's P10-B. The full-history fixtures rollup (105,509
  fixtures across 2019-01-01→2026-07-17, kickoff/status/team names 100%) is shipped in prod. This plan switches
  deployment-api's fixtures_browser.py off the ≤120-day day-walk onto the single rolled-up prod/catalog.parquet (the
  actual point of the operator's ask), then follows up with the UI span-cap relabel and the regen-freshness decision.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, deployment-api, instruments-service, unified-api-contracts, deployment-service]
scope: [engineer, admin]
tags: [data-status, sports, fixtures, catalogue, deployment-api, ux]
related:
  [
    /plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md,
    /plans/active/data_status_catalogue_true_source_phase2_2026_07_24.md,
    /plans/archive/issues/sports_fixture_round_not_captured_competition_phase_unknown_2026_07_17.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
assigned_role: ui_developer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Plan-hygiene line-cap remediation (2026-07-24) — forked out of
  data_status_page_ux_and_canonicalisation_2026_07_16.md's P10-B section per
  plans/active/issues/plan_line_cap_remediation_2026_07_23.md row #10 (bucket c, clean-partition). The parent plan's own
  3 open P10-B todos (below) are moved here verbatim, unedited; only frontmatter + this orienting header are new.
---

# Sports fixtures browser — switch to the single-file catalogue source

> **Human/LOCAL plan** (`assigned_vm: NA`) — forked 2026-07-24 out of
> `/plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md` (P10 / P10-B — Sports fixtures browser) as part
> of the plan line-cap remediation. That parent plan retains ~2000 lines of shipped history (P1-P10, including the full
> P10-B operator dialogue, the two corrections the operator forced, and the full-history rollup evidence) as the durable
> record — read it for full context. This child carries forward only the 3 still-open P10-B todos, moved **verbatim**
> from the parent — nothing summarized or rewritten.

## Codex SSOTs (this plan references, does not duplicate)

- `/codex/02-data/sports-2020-06-data-floor.md` — sports data-floor context for anything touching fixture history.
- `/codex/02-data/honest-absence-downstream-handling.md` — `venue_id=""` / honest blanks in the `FixtureRow` mapping
  below (no fabricated values).
- `/codex/06-coding-standards/ui-testing-layers.md` — `[UI]` + `pw:L2` gate for the `FixturesBrowser.tsx` relabel todo.

## Background (orienting summary, not a relocation of history — see parent for the full P10-B record)

Parent plan's P10-B (operator round-3, 2026-07-17) already shipped: `CATALOG_COLUMNS` carries fixture scheduling fields
(`kickoff_utc`/`status`/`home_team_name`/`away_team_name`/`venue_name`/`round` — instruments-service@684a1b2b), a
`--since` full-history escape hatch (instruments-service@4a795c24), and the full `--since 2019-01-01` rollup itself —
**105,509 fixtures, 2019-01-01→2026-07-17, kickoff/status/team names 100%, zero leakage onto team/player grains**
(independently verified 14/14 PASS), with a rollback snapshot retained. What remains is switching the actual browser
(`fixtures_browser.py`) onto that rolled-up source, plus 2 small follow-ups.

## Open todos (moved verbatim from the parent, 2026-07-24)

- [ ] [BACKEND] P2. **Switch `deployment-api/services/fixtures_browser.py` to the single catalogue** (the actual point
      of the operator's ask — currently still the day-walk, @5815582). Design, verified against real data: read
      `prod/catalog.parquet` ONCE (schema-aware projection: `instrument_id`/`instrument_type`/`league_id`/
      `available_from`/`kickoff_utc`/`status`/`home_team_name`/`away_team_name`/`venue_name`/`round`), filter
      `instrument_type=="fixture"`, TTL-cache the PARSED frame (not per-query) since filtering becomes in-memory. Map →
      `FixtureRow`: `fixture_id`=`instrument_id`; `home_team_id`/`away_team_id` parsed from the id's `HOME_v_AWAY` (or
      UAC `build_team_id`);
      `venue_id`=""`(not carried — honest). **Filter AND group on`available_from`** — it is     the true fixture date, verified **17,064/17,064 (100%)** identical to the id's `:YYYYMMDD`suffix, zero drift.     Then`_MAX_WINDOW_SPAN_DAYS`
      (120d cap) can be **deleted** — it only ever existed to bound the day-walk read cost — which is what finally makes
      "all the fixtures" true. A half-written attempt was **reverted** (it broke the module; a broken file in a shared
      checkout fails every agent's QG) — start clean from @5815582.
- [ ] [UI] P3. Once P10-B backend lands: `FixturesBrowser.tsx`'s window note + span-cap warning (`MAX_SPAN_DAYS=120`)
      become wrong — the catalogue has no 120d bound. Relabel to the real coverage (full history after the rollup) and
      drop the cap warning.
- [ ] [DATA] P2. _(freshness caveat, decide before/with P10-B)_ The catalogue is regenerated by the rollup job, so a
      catalogue-backed browser is only as fresh as the last regen (the day-walk read live parquets). For a
      scheduling/reference view this is fine, but **live status (NS→FT) will lag**. Confirm the regen cadence and either
      accept + label it, or keep a live-day overlay for today's fixtures.

## Progress Log

_(none yet — this plan was created 2026-07-24 by the plan line-cap remediation split; the todos above carry their full
prior design history verbatim from the parent plan's Progress Log.)_
