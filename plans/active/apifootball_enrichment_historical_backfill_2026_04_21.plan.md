---
title:
  "API-Football Enrichment Historical Backfill — FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS / PLAYER_STATS /
  INJURIES"
priority: P0
status: active
owner: agent
created: 2026-04-21
locked_by: live-defi-rollout
locked_since: 2026-04-21
type: deployment
epic: none
completion_gates:
  code: none
  deployment: D3
  business: B3
repo_gates:
  - repo: deployment-service
    deployment: D0
depends_on: []
isProject: false
---

## PLAN-SIZING (Phase 0 — 2026-04-21)

**Plan tier source of truth:** Secret Manager holds `api-football-api-key` only (no tier metadata).
`instruments-service/docs/SPORTS_INSTRUMENTS.md` documents the secret name, not subscription level. **Documented API
caps (UAC):** `unified-api-contracts/unified_api_contracts/external/api_football/schemas.py` and
`registry/venue_rate_limits.py` — **100 req/day (free), 7500/day (paid / Pro)**. Vendor “Ultra” (~75000/day) is not
encoded in UAC; **confirm live tier** from API-Football dashboard or from response headers (`x-ratelimit-requests-limit`
/ `x-ratelimit-requests-remaining`) on the first authenticated call.

**Live tier confirmed (2026-04-21 via GET /status):**

- Plan: **Mega** (higher than plan's worst-case Ultra estimate).
- Daily cap: **150,000 requests/day** (`x-ratelimit-requests-limit: 150000`, response `subscription.plan = "Mega"`,
  `requests.limit_day = 150000`).
- Per-minute cap: **900 req/min** (`x-ratelimit-limit: 900`).
- Subscription active through 2026-05-21 — backfill wave fits inside current billing cycle.

**Call budget (2019-01-16..2026-04-20, ~2650 dates):**

| Entity           | Order-of-magnitude calls | Notes                                    |
| ---------------- | ------------------------ | ---------------------------------------- |
| INJURIES         | ~2650                    | 1 call per date (league-agnostic window) |
| FIXTURE_STATS    | 150k–300k (plan est.)    | Per completed fixture                    |
| FIXTURE_EVENTS   | same band                | Per completed fixture                    |
| FIXTURE_LINEUPS  | same band                | Per completed fixture                    |
| PLAYER_STATS     | highest                  | Per player per fixture                   |
| **Total enrich** | ~600k–1.2M (plan est.)   | Serial across entities (singleton lock)  |

**Wall-clock vs daily cap (actual 150k/day Mega):**

- INJURIES: <2% of one day's quota — VM wall ~1–2h with pacing.
- Per heavy entity (STATS / EVENTS / LINEUPS / PLAYER_STATS): ~1–2 calendar days each at 150k/day.
- **Total serial wave: ~5–9 calendar days VM wall-clock** across all 5 entities under singleton lock.
- For historical reference only: 7500/day (Pro) → ~3–6 months; 75000/day (Ultra) → ~10–15 days.

**Sharding decision:** **A — One long-running VM per entity, strictly serial** (singleton lock on `af-backfill-*`). **B
(chunked multi-VM)** is rejected: shared API key rate limit yields 429 thrash without throughput gain (launcher
documents 2026-04-19 SFI incident pattern). At 150k/day we are network-bound not quota-bound for per-fixture entities;
singleton lock still enforced per 900 req/min burst cap.

## Context

Today's backfill work brought SPORTS FIXTURES from ~1% honest coverage to 99.2% for top leagues. But the SPORTS category
overall sits at **17.8% attempted / 15.6% captured**. The gap is the **per-fixture enrichment entities** —
FIXTURE_STATS, FIXTURE_EVENTS, FIXTURE_LINEUPS, PLAYER_STATS, INJURIES — where only the 2018-01-01..2019-01-15
historical backfill wave captured them for all leagues. 2019-01-16 → 2026-04-20 is uncaptured for those entities across
all ~80 leagues.

This is the single biggest SPORTS coverage gap. Closing it takes the category from ~15% to ~60-70% captured honest
coverage.

## Scope

Launch entity-scoped historical backfill VMs for:

- `FIXTURE_STATS` (goals, shots, possession, cards, etc.)
- `FIXTURE_EVENTS` (goals scored, subs, yellow/red cards timeline)
- `FIXTURE_LINEUPS` (starting XI + bench + formation)
- `PLAYER_STATS` (per-player per-fixture performance)
- `INJURIES` (per-date league snapshot)

For each entity, run over the full historical window (2019-01-16..2026-04-20, ~2650 dates). Per-fixture entities are
fetched PER FIXTURE — each league-date has N fixtures × 1 API call = expensive. Must parallelise carefully.

## Blast radius

- **deployment-service**:
  - `scripts/vm/launch-api-football-backfill-vm.sh` — already supports `--entity <NAME>`. No code change.
  - New orchestration script `scripts/vm/run-af-enrichment-backfill-plan.sh` (optional) that fires 5 VMs in sequence
    respecting the singleton-lock.
- **instruments-service**: no code change. Existing orchestrator handles entity-filter runs.
- **Manifest / rescan**: rescan will emit `empty_confirmed` for enrichment entities with no rows after the backfill.

## Cost + runtime estimate

API-Football shares one key across VMs (rate-limited). Singleton-locked launcher means **serialise, can't parallelise
across entities**.

Per entity × 2650 dates:

- FIXTURES-by-date: 1 call/date — covered by main backfill. Skip.
- INJURIES-by-date: 1 call/date → ~2650 calls. ~1 hour VM.
- FIXTURE_STATS: ~10 fixtures/date × 80 leagues (but adapter reads from GCS fixtures, only fetches for completed
  fixtures) → maybe 150k-300k calls total over the window. **Major cost — 10-20h VM or chunked**.
- FIXTURE_EVENTS: same shape.
- FIXTURE_LINEUPS: same shape.
- PLAYER_STATS: same shape.

Totals: ~600k-1.2M API calls. Depending on the API-Football plan, this costs real money. Plan assumes **Pro tier (7500
calls/day)** — 3-6 months to complete if daily-limited. **Ultra tier (75000/day)** — 10-15 days.

### Decision: sharding strategy

Cheapest path with a mid-tier plan: fire one long-running VM per entity, let it page through dates, accept the multi-day
runtime. Chunking across multiple VMs hits the shared-key rate limit and yields no speedup.

## Success criteria

- All 5 entities have `attempted` rows in the manifest for 2019-01-16 → 2026-04-20 at ≥95% of in-season (league, date)
  combinations.
- `empty_confirmed` distinguishes legitimately-zero-fixture days from failed-fetch days (existing manifest v5 contract).
- SPORTS category attempted-coverage lifts from 17.8% → 50%+ honest.
- No thundering-herd 429s in logs (singleton-lock enforced).
- All VMs self-delete on completion (wrapper fix from deployment-service beaa2e5).

## Phases

### Phase 0: Plan sizing [SEQUENTIAL — do first]

- [x] [AGENT] P0. Query API-Football current plan tier + daily rate limit (look in Secret Manager / check
      `instruments-service/docs/` for plan tier notes). Document in a PLAN-SIZING section at the top of this file.

- [x] [AGENT] P0. Compute expected VM wall-clock per entity from: number of in-season (league, date) combos ×
      fixtures-per-combo × 1 API call, vs. the plan's daily limit. Pick between: - A) One long-running VM per entity,
      serial - B) Chunked by year (3 VMs each covering 2-3 years) Document choice.

### Phase 1: INJURIES backfill [SEQUENTIAL]

- [x] [AGENT] P0. Cheapest first — INJURIES is 1-call-per-date (league- agnostic) so ~2650 calls = ~1 hour on mid tier.
      `bash launch-api-football-backfill-vm.sh --entity INJURIES 2019-01-16 2026-04-20` — **launched 2026-04-21 21:40
      UTC as `af-backfill-20260421-214057`** in `asia-northeast1-c` (e2-standard-2, singleton-lock held). Live tier Mega
      150k/day (confirmed via `/status`), 148k headroom.
- [ ] [AGENT] P0. Monitor VM to completion. Self-delete should fire.
- [ ] [AGENT] P0. Run rescan. Audit INJURIES manifest coverage.

### Phase 2: FIXTURE_STATS backfill [SEQUENTIAL, depends on Phase 1]

- [ ] [AGENT] P0. Per-fixture entity — cost scales with total fixture count in the window. Plan-sizing Phase 0
      determines chunks.
- [ ] [AGENT] P0. Launch one or more VMs per sizing decision.
- [ ] [AGENT] P0. Monitor + rescan + audit.

### Phase 3: FIXTURE_EVENTS backfill [SEQUENTIAL, depends on Phase 2]

Same shape as Phase 2.

### Phase 4: FIXTURE_LINEUPS backfill [SEQUENTIAL, depends on Phase 3]

Same shape.

### Phase 5: PLAYER_STATS backfill [SEQUENTIAL, depends on Phase 4]

Same shape. Most expensive — per-player per-fixture.

### Phase 6: Coverage audit [SEQUENTIAL]

- [ ] [AGENT] P0. Query deployment-api data-status endpoint. Confirm SPORTS category attempted ≥ 50%, captured ≥ 45%.
- [ ] [AGENT] P0. Spot-check 3 random dates per entity for data quality: INJURIES row counts plausible, FIXTURE_STATS
      columns populated, PLAYER_STATS covers lineup rows.

## Dependency graph

```
Phase 0 (sizing) ─► Phase 1 (INJURIES) ─► Phase 2 (STATS) ─► Phase 3 (EVENTS) ─► Phase 4 (LINEUPS) ─► Phase 5 (PLAYER_STATS) ─► Phase 6 (audit)
```

Strictly sequential per-entity due to shared API key rate-limit.

## Cross-refs

- Scheduling cadence codex: `codex/02-data/sports-scheduling-and-sharding.md` §§2.1, 4, 5.
- Launcher: `deployment-service/scripts/vm/launch-api-football-backfill-vm.sh`.
- Manifest v5 `empty_confirmed` contract: `codex/02-data/availability-manifest-and-data-status.md`.

## Out of scope

- Enrichment of pre-deployment 2018 dates (already captured by 2018 historical backfill).
- New launcher code — existing `--entity` flag suffices.
- Non-API-Football providers — separate plan (`non_apifootball_provider_backfill_launchers_2026_04_21`).
