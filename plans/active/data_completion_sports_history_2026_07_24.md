---
doc_type: plan
title: Data completion to 100% — Sports — Shipped History (forked from the sports data-completion plan)
summary: >-
  Archive-bound Progress Log history extracted verbatim from data_completion_sports_2026_07_24.md's 2026-07-24 line-cap
  remediation. Covers the earliest dated Progress Log narrative from "2026-06-24 DIAGNOSIS — golden FIXTURE_LINEUPS
  captured flat" back through "2026-06-21 SPORTS lane — RATE-LIMIT root-caused + fixed" — the campaign-opening
  rate-limit/thundering-herd fix, the odds-API credential/credits saga, the Live==Batch enum + connector key-resolution
  bugs, the enrichment OOM fix, the disparate-source concurrency fleet launch, skip-fresh verification, and the
  golden-window FIXTURE_LINEUPS force-flag diagnosis. Every item in this file is already checked-off `[x]` or pure
  narrative — zero open todos. Record-only; not intended for further action.
status: complete
nature: record
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts, deployment-service]
scope: [engineer, admin]
tags:
  [backfill, manifest, honest-coverage, data-completion, sports, data-correctness, history, plan-split, archive-bound]
related: [/plans/active/data_completion_sports_2026_07_24.md]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: docs_reconciler
drift_direction: advance-code
supersedes:
superseded_by:
depends_on:
source:
  [
    "Forked 2026-07-24 from data_completion_sports_2026_07_24.md's earliest Progress Log entries during the line-cap
    trim (parent was 1044 lines against the 1000-line cap).",
  ]
locked_by:
locked_since:
---

> **🟢 2026-07-24 history extraction** — this file holds Progress Log content moved VERBATIM out of
> `data_completion_sports_2026_07_24.md` (the "2026-06-24 ~05:35 — DIAGNOSIS" section through the final "2026-06-21 —
> SPORTS lane: RATE-LIMIT root-caused + fixed" entry) to bring that plan back under its 1000-line cap. Every line below
> already existed in the parent unchanged — no content was altered, only relocated. All items here are
> shipped/`[x]`/pure narrative; there are no open todos in this file. See the parent plan for current status and the
> still-open items.

# Data completion to 100% — Sports — Shipped History

### 2026-06-24 ~05:35 — DIAGNOSIS (no code bug): golden FIXTURE_LINEUPS captured flat because the running backfill uses `--force` (re-fetch already-captured cells)

**Root cause (evidence-backed, NOT a write-path bug):** the golden-window enrichment VM (`af-backfill-20260624-042815`)
was launched with
`python -m instruments_service --operation instruments --mode batch --asset-group SPORTS --start-date 2025-09-01 --end-date 2025-11-30 --force --sports-provider API_FOOTBALL --sports-entity FIXTURE_LINEUPS`
(verified in `gs://deployment-scripts-central-element-323112/vm-logs/af-backfill-20260624-042815/run.log`). The
`--force` flag → `redo_all=True` (`instruments_service/cli/instruments_handler.py:306` `redo_all = payload.force or …`),
which **bypasses the entire skip-already-captured pre-flight** in `sports_reference_fixtures.py:406`
(`if not redo_all and af_fid_to_league:`). So the VM re-fetches EVERY fixture in EVERY (date,league) cell — the run.log
shows `skipped_already_captured=0` on every date — and each fetch re-runs `record_captured`
(`sports_reference_fixtures.py:576`) on a cell that is ALREADY `captured`. The manifest grain for FIXTURE_LINEUPS is
**`(date, data_type, league_id)` per-league, not per-fixture**, so re-asserting an already-captured cell does NOT
increase the captured COUNT.

**The count is also at its structural ceiling.** Live `_index` golden-window (2025-09-01..11-30) FIXTURE_LINEUPS:
`captured=1,140 · empty_confirmed=7,427 · attempted_failed=18` → `captured+empty = 99.8%` of 8,585 (date,league) cells
already have a verdict. Per-league lineup parquets exist on disk (e.g.
`…/day=2025-09-30/.../entity=fixture_lineups/league=LA_LIGA/…`). Most "missing" cells are legitimately `empty_confirmed`
(error_reason `EXPECTED_NO_PROVIDER_COVERAGE`/`EXPECTED_NO_FIXTURE`/`SOURCE_RETURNED_ZERO`): 22 of 96 golden leagues
NEVER yield lineups. The ONLY genuinely re-fetchable gaps are the **18 attempted_failed cells** (+ rare empty→captured
if the source has since published). So 13.3% `captured/(captured+empty+failed)` for LINEUPS is near-final honest
coverage, NOT a stuck pipeline.

**FIX = corrected invocation, NOT code.** The `--force` re-run wastes the API-Football daily quota re-confirming done
cells. To make captured climb, target ONLY the open gaps: drop `--force` (so the skip-already-captured pre-flight
engages and only un-captured fixtures are fetched), and/or scope a re-attempt of the 18 `attempted_failed` cells. The
plan's existing line above ("multi-day skip-fresh re-runs") is the right lever — `--force` is the anti-pattern. Healthy
VMs left running (not stopped); the recommendation is the operator relaunch WITHOUT `--force` for any further enrichment
pass.

- [x] [DATA] P3. **Manifest hygiene — 5,690 of 7,427 golden FIXTURE_LINEUPS `empty_confirmed` cells carry a BLANK
      `error_reason`** (only 1,737 carry a typed reason `EXPECTED_NO_PROVIDER_COVERAGE`/`EXPECTED_NO_FIXTURE`/
      `SOURCE_RETURNED_ZERO`). Blank empty-reason should be `LegacyBlankErrorReasonError` territory — these are
      legacy/older-pass empties that escaped the typed-reason gate. Backfill typed reasons (likely
      `EXPECTED_NO_PROVIDER_COVERAGE` via the `sports_league_entity_coverage` registry) so the data-status page
      distinguishes "source said zero" from "unknown why zero". Repo: instruments-service. Provenance: 2026-06-24
      lineups capture-flat diagnosis. ✅ — instruments-service@74755fe (backfill_fixture_lineups_blank_reason.py added;
      classifies via is_league_entity_covered)

### 2026-06-21 22:55 — skip-fresh verified all sources; odds re-fetch FIXED; 2 follow-ups

**Operator Q "are we skipping already-done data?":** YES (confirmed via logs). Mechanism = writer reads canonical v9
manifest + `short-circuit: skipping orchestrator for date=X` (weather `OPEN_METEO short-circuit`, sfi
`SOCCER_FOOTBALL_INFO short-circuit`, odds `SKIP date=...: all venues fresh`). **EXCEPTION FIXED**: odds shards were
launched `--force` (bypass single-VM guard) which ALSO forces reprocess → re-fetching the done 13%. Added
`--allow-parallel` to the launcher (decouples guard-bypass from VM_FORCE), relaunched all 7 odds shards skip-fresh.
Weather has occasional Open-Meteo `400 Bad Request` per-location warnings (shard-isolated, non-fatal, recorded as failed
cells) — minor, backfill continues.

- [x] ✅ [DEPLOY] P2. Commit the odds-launcher `--allow-parallel` fix (deployment-service@scripts/vm/launch-mtds-sports-
      odds-backfill-vm.sh; backed up /tmp/odds_launcher_fixed.sh) once the deployment-service slot clone is clean —
      deployment-service@3448ce3 | Added ALLOW_PARALLEL var + --allow-parallel arg + guard bypass without VM_FORCE
- [x] ✅ [DATA] P3. Weather Open-Meteo 400s on some (lat,lon,date) — assess if systematic (param issue:
      `*_previous_day1` archive params) vs sparse-coverage locations; if systematic, fix the request params. Repo:
      instruments-service. — instruments-service@6c91bb3 | Root cause: (1) Previous Runs API (`*_previous_day1` vars)
      only served from 2024-01-01 — added `_PREV_RUNS_START` guard; (2) customer-archive-api returns 400 for pre-2024
      dates — added free-tier ERA5 archive fallback on 400.

### 2026-06-21 22:40 — DISPARATE-SOURCE CONCURRENCY (operator insight): all fixture-driven sources fired in parallel

With fixtures 100%, every fixture-driven enrichment source runs CONCURRENTLY on its OWN rate limit — sidesteps the
API-Football 300k/day cap for everything except API-Football itself. Launched the full fleet (14 sports VMs):

- **API-Football** (fixture stats/events/lineups/players): sports-enrich-2019-2022 + 2023-2026 (300k/day cap)
- **the-odds-api** (odds): mtds-backfill-odds-{2020..2026} (15M quota, no daily cap)
- **Open-Meteo** (weather, was 7%): weather-backfill-\* (free, keyless)
- **Transfermarkt** (player_values 9%, tm_leagues 0%): tm-backfill-\* (keyless scraper)
- **FootyStats** (0%): fs-backfill-\* (footystats-api-key)
- **SFI/soccerfootball-info** (sfi_progressive 12%, sfi_leagues 0%): sfi-backfill-\* + features-sfi-progressive-\*
  (soccer-football-info-api-key)
- **Live** odds stream: mtds-live-sports-\* (op=websocket-streaming)

Each source = own adapter (open_meteo.py / transfermarkt.py / soccerfootball_info.py / footystats.py / api_football.py)

- own API + own rate limit → true parallelism, no cross-source contention. This is the real throughput unlock: the
  API-Football daily cap only gates ITS 2 VMs; the other ~12 VMs fill weather/transfermarkt/SFI/footystats/odds with no
  daily ceiling. ONE full-fleet monitor (b1efcorlm) does a T+10 per-source health check (catches 401/scrape-block) then
  watches all to completion. Operator lever for the API-Football slice remains: bump to 1.5M/day.

### 2026-06-21 22:00 — "finish the current": parallelized for speed; honest completion picture

**Odds backfill 1→7 parallel year-shards** (`mtds-backfill-odds-{2020..2026}`, all RUNNING) — odds has ~15M req
remaining (no rate concern) so sharded with `--force` (idempotent re-fetch of static historical odds → guarantees 100%
coverage, ~7x faster than the single 304-chunk VM). **Enrichment** healthy: `sports-enrich-2019-2022` chunk 24/49,
`2023-2026` chunk 17/43 — finish current ranges ~2h. **Live** VM relaunched (`...213937`), op=websocket- streaming
mode=live (no 401 from the new VM; verifying publish).

**Coverage measured (availability_index):** core enrichment entities 8-13% captured-of-TOTAL (FIXTURE_STATS 13%,
EVENTS/LINEUPS 11%, MATCHES 13%, PLAYER_STATS 8%, ODDS 13%) — but TOTAL includes many no-fixture cells that become
empty_confirmed (raw log: "No fixtures for date → empty_confirmed markers"), so honest-cov is higher. Climbs as the 2
enrich VMs finish their chunks. **API-Football is daily-cap-bound (Custom300=300k/day, only 70k used — UNDER-used
because of empty-date stretches).** The 2 VMs finish their first pass ~2h; full multi-year enrichment to 100% needs
either more API-Football daily budget (operator → 1.5M/day = the 5x lever) or a multi-day multi-pass. ONE monitor
(b2tp3vezk) watches all 10 sports VMs, wakes on actionable event only.

### 2026-06-21 21:40 — ODDS API UPGRADED (blocker RESOLVED) + API-Football rate analysis

**Odds API blocker GONE:** operator upgraded the Odds API; `odds-api-key` (the secret the sports MTDS pipeline uses) now
returns HTTP 200 with **14,999,964 requests remaining**. Relaunched: odds backfill `mtds-backfill-odds-1`
(2020-06→2026-03, `--tier` bug already fixed) + fresh live VM `mtds-live-sports-odds-api-trades-20260621-213937` (old
one 401-dead since 19:07). Both verifying T+10min → live_odds_api rows + historical odds backfill resume.

**API-Football rate (operator Q "is 18k/30min maximising"):** NO per-minute (600/min vs 1200 ceiling, 704 free when
checked) — but per-minute is NOT the bottleneck. Plan=**Custom300** (300k/day); used 67.8k today, 232k left. The
per-fixture enrichment = millions of calls → **daily-cap-bound, inherently multi-day**. Pushing per-minute just exhausts
300k sooner then stalls to reset (same daily total). **The 5x completion lever = bump the daily cap to 1.5M/day**
(operator plan upgrade) — NOT a code/throttle/VM-count change. Throttle left at 0.12s (correct; lowering it is
pointless + 429-risky when daily-bound).

### 2026-06-21 — SPORTS lane: enrichment OOM fix + final autonomous state

**Enrichment OOM (fixed):** the per-fixture enrichment OOM-killed python (7.2GB anon-RSS) on the full-sweep default
`e2-standard-2` (8GB) — the in-memory fixtures catalogue + (league×entity) coverage map + per-fixture entity buffers
exceed 8GB. Relaunched both `sports-enrich-{2019-2022,2023-2026}` on **e2-standard-8 (32GB)** → stable (0 429s, fetches
climbing, entity-skip active). FOLLOW-UP: full-sweep/enrich launcher should default enrichment to e2-standard-8 (the
fixtures-only phase is fine on e2-standard-2; only the per-fixture enrichment needs the RAM).

**Final autonomous state (operator away 2h):** ALL code shipped + verified — 5 bugs, concurrency-safe throttle, 3
manifest migrations (odds AF 44%→7%, blanks 743k→0+dedup, 507k entity-coverage relabel + 92% player-stat skip),
Live==Batch wiring (LIVE_ODDS_API). ONLY blocker = **Odds API OUT OF CREDITS** (operator top-up; blocks live rows +
remaining odds backfill — code proven, VM running, emits on credit return). API-Football enrichment + fixtures fill is
rate-bound multi-day (1.2k/min ceiling, used fully, 0 waste). Sweep loop monitors VM health/OOM/credit-return.

### 2026-06-21 — SPORTS lane STATE SNAPSHOT (autonomous, operator away 2h) — for context-compression resume

**SHIPPED (all green):** `--tier` (deployment-service@b51729b) · silent-empty→attempted_failed (is@0db2450,+10 tests) ·
team_mapping GCS-429 write-once (is@865aea9) · **concurrency-safe self-enforced rate limiter** (is@e29ba65 — fixes the
burst→429→52s-minute-sleep thrash that capped enrichment at ~46/min vs 1200/min cap) · UAC entity-coverage map
(uac@9ea84499, sub-agent C). IS tarball rebuilt @e29ba65.

**RUNNING VMs:** odds-backfill `mtds-backfill-odds-{2020..2026}` (7, ODDS-API key, separate quota) · enrichment
`sports-enrich-{2019-2022,2023-2026}` (2, RELAUNCHED on fixed throttle — verify rate post-boot) · **sports LIVE** sports
LIVE producer (RELAUNCHED again post MTDS key-fix — see below; the `...184015` instance booted clean past the enum fix
but hit a SECOND bug: `OddsApi: no API key` because the connector referenced a nonexistent `MarketConfig.odds_api_key`
attribute; FIXED mtds@670be2f). Fixtures phase COMPLETE (265k captured / 1,356 leagues; VMs self-deleted).

**LIVE==BATCH (operator caught this) — UAC ENUM FIX LANDED:** sports had **0 `live_*` rows** — footystats fwd-poll wrote
`batch_*` (forward-over-future, NOT live). The true live producer
(`launch-mtds-live.sh --asset-group sports --shard-spec sports:odds_api:trades` → `odds_api_ws` WSFeedConnector →
`live_odds_api`) FAILED at boot with `No PipelineMode for source 'odds_api' in mode 'live'` — the `PipelineMode` closed
set had `BATCH_ODDS_API`/`REPLAY_ODDS_API` but no `LIVE_ODDS_API`. FIX (uac@249ca53f, LDR): added
`PipelineMode.LIVE_ODDS_API` + flipped `SOURCE_MODE_CAPABILITY["odds_api"]` to `{BATCH, LIVE, REPLAY}` + the test-side
SSOT `EXPECTED_SOURCE_MODE_CAPABILITY` + replaced `test_no_sports_source_is_live_yet` with
`test_odds_api_is_the_first_live_sports_source` (the other sports vendors stay live-less). `REPLAY_ODDS_API` already
existed (replay-capable). QG green (223s), source-mode + cassette tests pass. The live VM pip-installs UAC fresh at boot
→ it picks up the new enum once LDR has it; VM relaunched as `...184015` (same lowercase `odds_api` venue + 5-league
instrument-ids). Same canonical schema as batch (Live==Batch). cefi proved the live path works after its 5-bug first-run
chain (AG-agnostic infra bugs, fixed).

**SECOND LIVE-CHAIN BUG — MTDS connector key-resolution (FIXED mtds@670be2f, LDR):** post enum-fix, `...184015` booted
CLEAN through `websocket-streaming mode=live` + `DEPLOYMENT_STARTED` + wrote 5 per-VM manifest shards (the 5 leagues) —
proving the enum fix worked — but emitted `OddsApi: no API key — stream yields nothing` so 0 rows. ROOT CAUSE:
`odds_api_ws._get_api_key()` referenced `MarketConfig().odds_api_key`, an attribute that does NOT exist (the config
class is `MarketDataProviderConfig`, which exposes `odds_api_secret_name` not a resolved key); the bare `except`
swallowed the `AttributeError` → None → BLOCKED-CREDENTIALS message DESPITE the `odds-api-key` secret existing (32-char
value verified in Secret Manager). FIX: resolve via the canonical
`get_secret_client(project_id=cfg.gcp_project_id).get_secret(cfg.odds_api_secret_name)` (the same pattern the WORKING
batch `OddsApiAdapter` + `DatabentoBaseClient` use). 30 connector unit tests pass; QG green; basedpyright clean on the
change (the 3 file-level Any errors are pre-existing JSON-parse lines, not the edit). The VM pip-installs MTDS fresh at
boot → relaunched to pick up `670be2f`.

**THIRD (TERMINAL) BLOCKER — The Odds API credits EXHAUSTED → `BLOCKED-CREDENTIALS` (operator top-up, 2026-06-21):**
with the key-fix live, VM `...190258` now SENDS the key — the API authenticates the request but returns **HTTP 401
`OUT_OF_USAGE_CREDITS`**. Verified directly: the `odds-api-key` secret is a VALID key (the free `/v4/sports/` list
endpoint returns 200 with EPL/Serie-A active), but the credit-costing `/v4/sports/{sport}/odds` endpoint returns
`{"error_code":"OUT_OF_USAGE_CREDITS"}` with headers `x-requests-used: 5000060 / x-requests-remaining: -60`. The 7
odds-BACKFILL VMs (2020-2026 historical odds) drained the entire quota on the SAME `odds-api-key` secret. **The full
code+infra live path is now PROVEN end-to-end** (enum ✓ + key-resolution ✓ + DEPLOYMENT_STARTED + per-VM manifest shards
written + graceful 401 honest-absence, 0 crashes) — the ONLY remaining gap is credits. The connector polls every 60s and
will emit `live_odds_api` rows with NO further code change the moment credits return. VM `...190258` LEFT RUNNING so it
auto-produces on top-up.

> **CREDENTIAL APPROVAL REQUEST — odds-api-live-credits (operator action 2026-06-21):** Vendor: The Odds API
> (https://the-odds-api.com/#get-access). What I need: top up / upgrade the `odds-api-key` Secret-Manager key's monthly
> credit quota (current usage 5,000,060 — quota fully consumed by the 2020-2026 historical backfill on the SAME key). A
> SEPARATE live-only key (its own quota) would prevent the backfill from re-draining live; otherwise live + backfill
> must share. Unblocks: the FINAL `≥1 live_odds_api` sports row (Live==Batch sports gate). Without it: VM `...190258`
> stays up
>
> - honest-absences (0 rows) until credits return — no further code work needed.

**3 MIGRATION SUB-AGENTS in flight (opus), IS ships BLOCKED on a LIVE foreign UTL WIP**
(`manifest_writer/_writer_captured.py`, peer actively editing — do NOT stomp; their tracked waiters fire when UTL goes
clean):

- **A** (agentId in transcript): canonicalise legacy `batch_instruments_service` sports rows → `batch_<source>` + fill
  blank reasons → fixes the 130,828 blank-reason cells + the ~1.16× double-count (pipeline_mode dedup-key drift). IS
  migration script.
- **B**: odds (book×league) observed-coverage map + sentinel wiring + migration → fixes the ~72% mislabelled
  `attempted_failed` (Kalshi/Polymarket removed as they're prediction-markets not Odds-API). UAC+MTDS.
- **C** (a2c87b13142bd5311): UAC@9ea84499 shipped — `is_league_entity_covered(league,entity)` + new
  `EmptyConfirmedReason.EXPECTED_NO_PROVIDER_COVERAGE`. Dry-run: **~92% of leagues never yield player-stats** → skip
  kills the waste; **506,959 cells** relabel → expected-empty. IS write-path + migration ready, pending UTL-clear.

**WRITE-PATH AUDIT (regression-proof):** record_empty rejects blank (`LegacyBlankErrorReasonError`) + invalid reasons;
`pipeline_mode: PipelineMode` REQUIRED; schema_version=9. So all issues are LEGACY data → migrations fix them; no live
regression.

**NEXT (autonomous loop, `/tmp/sports_autoloop.sh` watcher armed):** (1) verify sports live ≥1 row; (2) verify
enrichment post-throttle rate (if still latency-bound/sequential → the per-fixture fetch needs concurrency = next fix);
(3) when UTL clears → resume A/B/C → ship + run their `--apply` migrations (snapshot first) → honest-cov jumps to
reality; (4) once C's entity-skip lands → rebuild tarball + relaunch enrichment (drops ~92% wasted player-stat calls).
Raw backfill is rate/credit-bound (multi-day, API ceiling) — running efficiently.

### 2026-06-21 — SPORTS lane (/autonomous, Opus): odds flowing; API-Football credential block + silent-empty bug FIXED

**Shipped:** `--tier` launcher bug (deployment-service@b51729b). Silent-empty manifest bug (instruments-service@0db2450,
QG-green sentinel b5b8b72; direct-LDR under dirty-deps carve-out — UAC/UTL dirty with concurrent provenance WIP).

**MTDS odds = HEALTHY + flowing hard.** 7 year-shard VMs `mtds-backfill-odds-{2020..2026}` (--force, 2020-06→2026-06)
RUNNING, writing real bookmaker odds (WilliamHill/DraftKings/Ladbrokes/… EPL); odds-2026 124k rows, odds-2020 30k,
climbing. `pipeline_mode=batch_odds_api` → `market-data-tick-sports-prd-…` (canonical consolidator ENABLED \*/1).

**Root cause (operator-confirmed): IS fixtures gap = CREDENTIAL block, now lifted.** Full-sweep fetched 0 fixtures/date
→ `errors.plan` (free API-Football, dates 2026-06-20..22 only). Operator upgraded → **Custom 1200 r/min, 5 seats, 300k
r/day** (re-tested: 2024-01-13 → 927 fixtures). Killed 8 false-writing full-sweep VMs (each wrote only ~2 dates false
`empty_confirmed` before kill → small blast radius).

### 2026-06-21 — SPORTS lane: RATE-LIMIT root-caused + fixed (operator: "only ~1k req/hr vs 1.2k/min — way too slow")

**Root cause (the throttle thundering-herd):** sports adapter `_MIN_REQUEST_INTERVAL=0.1s` = 600 req/min PER VM. 8
all-entities full-sweep VMs × 600 = 4800/min slammed the API-Football **1.2k/min** cap → every VM 429s → the adapter's
"sleep to next UTC-minute boundary" (`base.py` `_get_with_retry`) → all 8 idle ~50s, wake together, overshoot again →
fleet collapsed to **~22 req/min** (operator's dashboard: ~1k/hr). The heavy load was the **per-fixture enrichment**
fan-out (`/fixtures/players`, `/fixtures/events`, lineups, stats — N calls/fixture).

**Fix (operator-steered: fixtures-first + fewer VMs):** killed the 8 thrashing VMs. Relaunched **2 FIXTURES-ONLY VMs**
(is-gap-fill `--entity FIXTURES`, split 2019-2022 / 2023-2026) = 2×600/min ≈ the 1.2k/min cap with **NO thundering
herd**. **Verified flowing at full speed, zero rate-limiting** ("Fetched 639 fixtures for date=2019-03-02", multiple
dates/sec). FIXTURES = ~1 call/date (~2920 total for 8yr) → catalogue fills in **minutes**, not days. Also shipped
full-sweep `--entity` flag (deployment-service@4caeaf3) for fixtures-first phasing.

**Architecture confirmed (operator's Q): enrichment reads fixtures from GCS** — `_per_fixture_gcs_fast_path`
(process.py:191) lets per-fixture entities read fixture IDs from GCS, so fixtures-first composes: Phase-1 FIXTURES
(fast), Phase-2 enrichment (heavy) reads the Phase-1 GCS fixtures. The all-entities full-sweep did NOT use this split
(grabbed fixtures + enriched inline per date → the thrash).

**Phased plan (autonomous):** Phase-1 FIXTURES (running, ~mins) → Phase-2 ENRICHMENT (per-fixture entities, 2 VMs at the
1.2k/min cap, GCS-fixture fast path) = **multi-day, rate-cap-bound** (millions of per-fixture calls; 300k/day now,
operator upgrading to 1.5M/day; per-minute 1.2k is the binding constraint — no agent can exceed the API ceiling, but 2
VMs use it FULLY without thrash). Odds backfill (7 VMs, separate ODDS-API key, no contention) + live (footystats +
scheduler) continue. Background monitor armed: fixtures-complete → auto-launch enrichment.
