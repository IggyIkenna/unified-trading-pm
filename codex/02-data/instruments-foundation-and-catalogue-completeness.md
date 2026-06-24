# Instruments Foundation & Catalogue Completeness — the standard for EVERY asset group

> **Status:** STANDARD (codified 2026-06-24, operator-directed reset). **Scope:** cefi · defi · tradfi · sports — this
> doc **dictates the same process for all four**. "tradfi perpetuals" (single stocks / commodities on Binance) are
> technically **cefi** and are covered under the cefi venue universe. **Why this exists:** reference data (the
> instruments catalogue) is the FOUNDATION market-tick-data filters against. A market-data coverage number computed
> against an incomplete or stale catalogue is meaningless. We kept chasing MTDS coverage while the instruments
> foundation had day-gaps, a paused daily capture, and late MVP tags — that is backwards.

---

## 0. The hard dependency order (gated — operator sign-off at EVERY gate)

You may **not** start step N+1 until step N is GREEN-audited and the operator has signed off. No parallel-up across
these steps for a given asset group.

| Gate   | Step                                                                                                                                                                                                                          | Done-when (audited, not asserted)                                                                                                                                                                         |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **G1** | **instruments-service correct per-day, historically** — the code that fetches + writes per-(day,venue) instruments is right, deterministic, and **landed on LDR**.                                                            | Code on LDR + QG-green; a single day re-run is byte-reproducible; no junk/test symbols; per-instrument fields (available_from, type, symbol, MVP, universe-tag) correct.                                  |
| **G2** | **Backfill it** — every instrument × venue × **day** × all years (genesis→today), no gaps.                                                                                                                                    | `day_coverage = 100%` (see §2): every expected venue-day present; per-venue **cumulative** universe monotonic; weekly type+symbol completeness met; universe depth (MVP+Expanded+stocks/commodities) met. |
| **G3** | **Aggregate** — run the lifecycle roll-up (`build_instrument_catalogue.py`) AND **verify the scheduler actually runs it, on the latest code, doing what we expect**.                                                          | Catalogue `available_from`/`available_to`/MVP correct for a sample; the Cloud Run job's image == latest LDR/main; the scheduler fired today and produced today's artefact; no silent staleness.           |
| **G4** | **THEN start MTDS** — market-tick-data only fetches instruments that are **in the catalogue for that day's availability window**. The capture code _filters the catalogue_ per-day; it never enumerates a raw venue universe. | A spot-check proves MTDS attempts == catalogue-active-for-day (no pre-listing, no post-expiry, no out-of-universe).                                                                                       |
| **G5** | **Verify MTDS coverage rises as expected** — `depth_coverage` on market-data climbs day-by-day with no new honest-absence/failed surprises.                                                                                   | MTDS day+depth coverage trends up; residual gaps each have a typed, understood reason.                                                                                                                    |

**Anti-pattern (what we did wrong):** running G4/G5 (MTDS backfill + coverage chasing) while G1–G3 were red. Never
again.

---

## 0.5 Observability is a LAUNCH PRECONDITION — no fire-and-forget (HARD RULE)

Operator 2026-06-24: every backfill / roll-up / capture job — **for every asset group** — MUST ride the
deployment-observability stack we already built. No more blindly launching VMs + SSHing + hoping. **A job that is not
registered + observable does not launch.** This is a **G1/G2 gate item** (the launch machinery must be observable BEFORE
the backfill runs). Concretely, every instruments backfill VM, lifecycle-roll-up Cloud Run job, and MTDS backfill MUST:

1. **Register as a classified `DeploymentTarget`** — via
   `deployment_service.deployment_classification.classify_deployment_target` (raises `UnclassifiedDeploymentError`,
   never a silent default) + the `cloud_run_job_registry.CLOUD_RUN_JOBS` registry (jobs) / VM `lifecycle_class` +
   `VM_PREFIX_TO_BUCKET` (VMs). A scheduler/launcher without a registry entry fails CI.
2. **Heartbeat + lifecycle events** — `ServiceBootstrap` (STARTED / STOPPED / FAILED) + `log_event` (11 lifecycle
   events) + the 60-s `PIPELINE_HEARTBEAT` worker-life marker + ≥1 progress/hour. No silent run.
3. **Error → Slack** — any error in a job's logs pages `#data-pipeline-alerts` (the `DP_*` heartbeat-watcher /
   exit-code-monitor / monitoring-deadman + manifest-staleness watchers). A self-deleting VM MUST persist its terminal
   `exit_code` to the GCS `run.log` (so OOM/exit-137 is distinguishable from clean completion) and advance a log-mtime
   marker (so a hang is detectable).
4. **Show in the deployment-UI cockpit, CLICK-THROUGH to logs (this is the point)** — every instruments/MTDS backfill +
   roll-up classifies under the **BATCH** umbrella (operator 2026-06-24 — historical backfills/roll-ups are batch, not
   paper-_trading_) and appears in `/deployments` under the **batch** tab via `GET /api/deployments/inventory` +
   `…/umbrella/batch/summary`. What matters is the **click-through**: from the cockpit you drill into the job → its live
   logs / heartbeat / status / terminal `exit_code` — no SSH. **A launched job you cannot click through to in the
   cockpit is a defect, not a quiet success.**
5. **Use the stack, not SSH** — the fleet monitors, manifest aggregators, and escalation tools are how we watch these;
   SSH-and-hope is banned. Composes with the CLAUDE.md HARD RULES "No fire-and-forget VM launches (T+10min verify)" +
   "self-deleting VM monitor must check terminal exit_code + log-mtime advancement".

SSOT: `codex/05-infrastructure/deployment-observability.md` +
`plans/active/deployment_observability_parity_live_batch_paper_2026_06_22.md`.

---

## 1. The completeness checks (instruments-service, per AG, per venue)

A per-venue **coverage %** is necessary but NOT sufficient. The full standard a venue/AG must pass:

1. **No day-gaps.** Every day from each venue's **genesis** to today is present. A missing day is a **0%** cell, never
   silently absent (see §2 — the expected-universe must be materialised).
2. **Per-venue CUMULATIVE universe is monotonic — a MEASURED day-over-day drawdown check (HARD).** Compute, per venue,
   the cumulative instruments-ever-seen series across days; it must be **monotonic non-decreasing — every day ≥ the
   previous day** (new listings only ever add). **Any negative day-over-day delta in the CUMULATIVE count is a drawdown
   = a hard capture-correctness defect** (we "lost" instruments we had already seen — a gappy/partial day's snapshot
   over-wrote history) → flag + block, never silently accept. Track it as a first-class health metric: per-venue
   cumulative series + the count and magnitude of any cumulative drawdowns (target = **zero drawdowns**).
   - **Active vs cumulative (the distinction that makes the check honest):** the per-day **active** count MAY drop, but
     every active drop must NET to a **typed reason** — cefi/tradfi: a real delisting (`available_to` set); DeFi:
     delisting OR TVL-below-threshold (`NOT_ENOUGH_TVL`, §1.3). An active-count drawdown with **no** delisting/TVL
     reason = capture instability, flag it. (Audit 2026-06-24: cefi venues showed thousands of day-over-day active drops
     — each MUST reconcile to a real delisting vs a capture bug; an unreconciled active drawdown is a G1 defect.)
   - **Per-day instrument count should trend UP or flat** (new listings outpace delistings in a growing market); a
     sustained per-day downtrend that isn't explained by typed delistings/TVL is a capture-stability alarm, not a market
     signal — investigate the snapshot, don't accept it.
3. **Weekly type + symbol completeness.** For every week, every venue carries **all the instrument _types_ it should**
   (PERPETUAL / FUTURE / OPTION / SPOT_PAIR / COMBO as applicable) and the **expected symbol set** — not a thinned
   subset.
   - **DeFi nuance (HARD):** a per-day **active** drop is NOT only a real delisting (§1.2). For a DeFi **pool**,
     "listed" (the pool contract exists, `available_to=None`) and "above the TVL threshold today" are **different
     states** — liquidity is **continuous and can drop/recover day-to-day**. So a pool dropping out of the per-day
     active set because its TVL fell below threshold is a **legitimate `EXPECTED_NOT_ENOUGH_TVL` day, NOT a delisting
     and NOT a capture bug**. The §1.2 "active-drop-only-from-delisting" rule applies to cefi/tradfi/sports (binary
     listing); for DeFi the active-drop reason set is
     `{delisting (available_to set), TVL-below-threshold (NOT_ENOUGH_TVL)}`. Never flag a DeFi TVL-drop as a capture
     defect.
4. **Universe depth.** All universes are dumped, not just MVP: **MVP + Expanded Universe + venue-specific** (Binance
   single-stocks, stock-perps, and commodities like XAU/XAG are in-scope and **were** present in the 2026-06-24 audit —
   keep them).
5. **Noise guard.** No junk / test / malformed symbols (the 2026-06-24 audit found CJK/meme test bases leaking into
   Binance-Futures). A junk symbol is a capture-correctness bug at G1.

---

## 2. The honest-coverage definition — LAYERED, and IN LINE with the UI (HARD RULE)

Operator 2026-06-24: **every coverage number we compute must be the SAME number the deployment-UI shows.** No ad-hoc
scripts that diverge from the UI. The mechanism already exists — use it, do not bypass it:

- **SSOT:** `unified_api_contracts.canonical.crosscutting.honest_coverage.compute_honest_coverage` (impl in
  `_honest_coverage_logic.py`). Its own contract: _every numerator/denominator computation in the workspace MUST flow
  through it so deployment-api / data-status / UI align._ Plan: `honest_coverage_formula_consolidation_2026_05_19.md`.
- **The expected-universe MUST be materialised** (writer-driven, never re-derived by a reader — see
  `availability-manifest-and-data-status.md`): missing days/instruments are seeded as `expected_unattempted`
  (pending_fetch), so a gap **drags the denominator down** instead of being invisible. The 2026-06-24 audit's "99.9%"
  was dishonest precisely because the 3 missing days (06-19/20/21) were **absent**, not seeded as 0%.

**Two layered numbers per AG (operator decision 2026-06-24), both via the SSOT:**

| Number               | Numerator / Denominator                                                                                                                                                                     | Catches                                                                |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **`day_coverage`**   | captured-or-honestly-empty **venue-days** / **expected venue-days** (Σ over venues of `today − venue_genesis`)                                                                              | "a day has nothing" — day-gaps (06-19/20/21).                          |
| **`depth_coverage`** | captured **instruments** / **expected instruments** per (venue, day) where expected = the full universe that venue should list that day (types + symbols + MVP/Expanded/stocks/commodities) | "the day is there but thin" — partial universe, missing types/symbols. |

Both surface together in **manifest → `/data-status` → deployment-API → deployment-UI**, per AG and per venue, so the
operator reads one consistent, real number. A green `day_coverage` with a low `depth_coverage` is the explicit signal
"every day present, but days are under-populated."

### 2.1 The expected-universe ORACLE — the `depth_coverage` denominator (the hard part)

`depth_coverage` is only as honest as the **denominator**: "how many instruments SHOULD venue V have listed on day D?"
That number is **external truth**, not our own capture (using first-seen-in-our-data is **circular** — if we missed the
listing day, our "genesis" is wrong and the gap hides itself). Operator 2026-06-24: we have to account for this
properly.

Two sub-oracles, both **time-varying**:

1. **Per-instrument true GENESIS (listing date).** For e.g. **Binance `AAPL` perpetual** we must know the _exact_ day it
   was added on the venue — otherwise it never enters the expected set and its missing history is invisible to coverage.
   `available_from` must be reconciled to **venue truth** (exchange listing announcement / venue reference data with the
   real list date), not the first day it happened to appear in our (gappy) capture. A drift between venue-truth-genesis
   and first-seen-in-capture is itself a G1/G2 defect to flag.
2. **Futures EXPIRY-SCHEDULE rules (per venue, time-varying exchange rules).** For dated futures/options the expected
   set on day D is **governed by the exchange's contract-listing rules** — e.g. which weeklies/monthlies/quarterlies a
   venue lists, the roll schedule, how many forward expiries are simultaneously listed. **These rules change over time**
   (a venue adds a new tenor, changes the roll, lists a new product class). So the expected-futures-universe is a
   function of `(venue, date, listing_rules_as_of(date))`. We must **encode these rules, versioned by effective-date**,
   so for any historical day we can compute "these exact expiries should have existed" — and therefore honestly score
   whether we captured them.

**Implication (must be explicit in the plan):** `depth_coverage` ships in **two tiers**:

- **Tier-A (proxy, interim):** denominator = the venue's own per-day active set as the venue reported it (or our
  catalogue's active-on-day) — catches thin-vs-full _within what we know_, but is blind to instruments/expiries we never
  saw. Clearly labelled as a proxy in the UI.
- **Tier-B (true oracle):** denominator = venue-truth genesis (1) + encoded time-varying expiry/listing rules (2). This
  is the real "did we get everything the exchange ever listed" number. Building the oracle (per-venue listing-rule
  registry + genesis reconciliation) is a first-class deliverable, **not** a footnote — a venue/AG is not "complete"
  until Tier-B is green.

The registry of venue listing/expiry rules lives in UAC (alongside the venue capability declarations) so MTDS, the
catalogue roll-up, and the coverage computation all read the SAME rules — no per-consumer re-derivation.

**DeFi's oracle is the 3rd sub-oracle — the per-date TVL threshold (operator decision 2026-06-24,
`window=expected, per-date-TVL=captured`).** DeFi has no futures expiry rules; its time-varying per-day listing rule
**is liquidity**:

1. **Genesis = on-chain pool-creation date** (the creation block) — external truth, knowable, never
   first-seen-in-capture.
2. **Per-date TVL threshold = the DeFi analog of the expiry-schedule rule.** The catalogue's
   `available_from→available_to` **window defines EXPECTED** (every pool seeded `expected_unattempted` for every
   in-window day → the `depth_coverage` denominator). **Within the window, the per-date TVL decides the
   captured-state**, a **3-way** (vs the binary captured/empty elsewhere): `captured` (met TVL that day + data fetched)
   · `EXPECTED_NOT_ENOUGH_TVL` (in-window but TVL below threshold that day — a genuine, honest empty, the
   liquidity-discontinuity) · `SOURCE_RETURNED_ZERO` (met TVL, source genuinely returned nothing, with FetchEvidence).
   The per-date TVL signal is **materialised by the instruments-service per-day enumeration** (it MUST be complete —
   capturing ALL above-threshold pools that day; an under-enumerated per-date snapshot, e.g. 316 where the window says
   1,425, is a G1/G2 defect that strands real pools as false NOT_ENOUGH_TVL). Capture filters on this same set so
   captured (pool,date) keys coincide with the EU seeds — the cell-key alignment is the whole point (the 2026-06-24 DeFi
   stall was capture fetching a broad top-N pool set whose (pool,date) cells never coincided with the window-seeded EU).
   This registry (per-protocol×chain TVL threshold, versioned by effective-date if it changes) lives in UAC like the
   cefi/tradfi listing rules.

### 2.2 Consolidation & reconcile — incremental is blind to unexpected-missing (HARD)

Operator 2026-06-24: "do we `--force` or just on unexpected missing shards — and how do we know the drilldown is right?"

- **Incremental merge alone LIES.** The consolidator's incremental path merges the shards that _exist_; it cannot see a
  shard that _should_ exist but doesn't (a VM died pre-write, a shard was deleted). The ONLY way an unexpected-missing
  shard is detectable is by reconciling against the **materialised expected-universe** (§2/§2.1): every expected
  `(venue × day [× instrument])` cell must resolve to a shard/row; an expected cell with no shard = an unexpected gap →
  scored **0% in `day_coverage`** AND queued for re-fetch.
- **Strategy:** **incremental** for the daily steady-state (cheap); **`--force`/reconcile** after any backfill and on a
  periodic cadence, **scoped to the affected window** (never a blind whole-corpus `--force` — that OOM'd at 32Gi; clip
  the from/to range, cap cells via the purge discipline). The reconcile compares **actual shards vs expected-universe**
  — that pass is what _discovers_ unexpected-missing, not a reaction to already-known gaps. So: not "`--force` only on
  unexpected missing" — you cannot know they're missing without the reconcile; the reconcile IS the discovery.

### 2.3 Drilldown-correctness guard — prove the cockpit number is the truth (HARD)

The deployment-UI cockpit drilldown is only trustworthy if proven, on three legs:

1. **One number, not two.** The UI renders the `compute_honest_coverage` SSOT value off the manifest — it **never
   recomputes its own**. One number from manifest → `/data-status` → API → cockpit.
2. **Reconciliation guard.** A check independently recomputes coverage from the **raw GCS parquets** and asserts it
   equals the manifest/SSOT/UI number (ε=0); wired as a **QG step + a watchdog → `#data-pipeline-alerts` on drift**.
   This is the proof the displayed number matches ground-truth, not a stale/divergent cache.
3. **Freshness + traceability.** The consolidator-staleness watchdog keeps the UI non-stale; a cockpit click on a
   venue-day resolves to the **actual shard/instruments** in GCS so any cell is traceable to source.

"The drilldown is right" ⟺ reads-SSOT **AND** reconciliation-guard-green **AND** manifest-fresh. Without the
reconciliation guard the cockpit is an unverified number we are merely trusting.

---

## 3. Per-asset-group application (same process, AG-specific universe)

The process (§0 gates + §1 checks + §2 layered coverage) is identical; only the universe + source differ:

- **cefi** — venues Binance(-Futures/-Spot), Bybit(-Spot), OKX(-Spot/-Swap/-Futures), Deribit, Kraken(-Spot/-Futures),
  Bitget(-Spot/-Futures), Upbit, Coinbase(-Spot/-Futures), Aster, Hyperliquid. Types PERPETUAL/FUTURE/OPTION/SPOT_PAIR/
  COMBO. Universe = MVP + Expanded + **Binance single-stocks / stock-perps / commodities (XAU/XAG)**. Source = Tardis +
  venue reference APIs. Genesis ≈ 2019-03-30 (per venue). **Execute cefi FIRST.**
- **defi** — per protocol × chain; pools/tokens/markets. Source = subgraphs / RPC. Genesis = on-chain pool-creation date
  (record-zero-rows venue-launch-aware). Same gates + layered coverage, **plus the DeFi-specific deltas**: (a) per-date
  TVL threshold is the listing-rule oracle (§2.1) — `window=expected, per-date-TVL=captured`, 3-way
  captured/`NOT_ENOUGH_TVL`/`SOURCE_RETURNED_ZERO`; (b) active-drop from TVL is legitimate, not a delisting (§1.3 DeFi
  nuance); (c) **dual-form instrument_id** — canonical `pool_address.lower()` (the machine/manifest/EU-seed + capture
  key, the SSOT) **AND** a human-readable `glued_pair_id` (`PROTOCOL-CHAIN:POOL:PAIR:FEE`) with a bidirectional
  converter (UI/readability only — never the cell key); (d) **G4 catalogue-as-filter is the load-bearing step for DeFi**
  — capture MUST query exactly the catalogue pools in-window per (venue,chain,date), never the subgraph's own
  top-N-by-TVL (that broad set's (pool,date) cells never coincide with the EU seeds); (e) every catalogue protocol×chain
  must have a subgraph/RPC source wired (a catalogue venue with no source = a G1 gap, e.g. TRADER_JOE_V2 / UNISWAP_V4 /
  ORCA / KAMINO / VELODROME_V2 / RAYDIUM were uncovered in the 2026-06-24 audit) — if genuinely none exists,
  `BLOCKED-CREDENTIALS`/known-gap, never silently dropped; (f) The Graph skip-based pagination caps at ~5000 → use
  **timestamp-cursor pagination** so a queried pool's full day captures (mtds@08b45468). DeFi SSOT:
  `codex/02-data/defi-canonical-naming-ssot.md` + plan `defi_instrument_catalogue_and_capture_pipeline_2026_06_23.md`.
- **tradfi** — Databento universe (GLBX.MDP3 CME futures, DBEQ.BASIC US equities, XCBF.PITCH CFE/VX). Per the operator,
  "tradfi perpetuals" (single stocks/commodities on Binance) are **cefi**, not here. Same gates + layered coverage.
- **sports** — **fixtures ARE the instruments** (the catalogue atoms); universe = the **~101 canonical MVP leagues**
  (UAC `LEAGUE_REGISTRY`), NOT the raw provider league list. The fixture catalogue + genesis come from **api_football**
  (FIXTURES/INJURIES/FIXTURE_STATS/LINEUPS/PLAYER_STATS/EVENTS); footystats (MATCHES/STANDINGS/TEAMS + in-house
  PREDICTIONS), understat (XG/XG_SHOTS), transfermarkt (PLAYER_VALUES), open_meteo (WEATHER), soccer_football_info all
  enrich **OFF the canonical fixtures**. `candidate_parquet_paths()` universe + same G0 gates + layered coverage.
  Sports-specific rules (codified 2026-06-24):
  1. **MVP-SCOPE the enumeration — non-canonical leagues are NOISE to delete, not capture.** The expected-universe MUST
     be seeded ONLY for the ~101 canonical leagues. Audit 2026-06-24: api_football FIXTURES enumerated **1,531 leagues
     (94 canonical + 1,437 non-canonical = ~106k noise rows)** — those 1,437 inflate every coverage number + pollute the
     catalogue and must be deleted/excluded. A non-MVP league in the manifest is a G1 enumeration bug.
  2. **Per-SOURCE coverage is a SUBSET — a source not covering a league is HONEST ABSENCE, never a failure.** Each
     enrichment source covers only a subset of the canonical leagues. A league a source doesn't cover →
     `record_empty(EXPECTED_NO_PROVIDER_COVERAGE)` via UAC `is_league_entity_covered` (the per-(league,entity) coverage
     map) — NEVER `attempted_failed`, never retried. A 404 on a non-covered league is expected, not a fetch failure (the
     sports realisation of "not every venue lists every instrument"). The error branch MUST consult the coverage map,
     not blanket-fail all expected leagues on one error.
  3. **ODDS are MTDS, NOT instruments-service.** Any bookmaker odds (footystats OR odds-api) are market-tick-data. The
     ONLY footystats odds-LIKE data_type that belongs in IS is **`PREDICTIONS`** (footystats' in-house prediction model
     — a derived fixture attribute). The misplaced IS footystats `ODDS` (194,789 rows, 2026-06-24) is wiped; odds-api in
     MTDS (211,299 captured / 0 failed) is the canonical sports odds source.
  4. **`depth_coverage` Tier-B = the FIXTURE-COMPLETENESS ORACLE.** Unlike cefi/defi we cannot run a monotonicity check
     on daily fixtures, but we CAN validate captured fixtures against **known per-league season structure** (external
     truth): `n_teams` → `expected_fixtures` (double round-robin = `n_teams×(n_teams−1)`), per-team game count,
     promotion/ relegation extras, season window + expected gaps (transfer windows / off-seasons), and **reschedule =
     the FINAL kickoff time, not the initial** (a moved match counts at its new time — what downstream odds/enrichment
     key off). Registry in UAC alongside `league_data.py`/`season_dates.py`. SSOT plan:
     `plans/active/sports_fixture_completeness_oracle_2026_06_24.md`.
  5. **Full-range FIXTURES first (G2) — `empty_confirmed` is skip-existing's blind spot.** A wrongly-`empty_confirmed`
     historical cell is SKIPPED by the skip-existing backfill (empty = "not missing") → stuck forever; it needs a
     **scoped `--force`** (the §2.2 reconcile-discovers-then-force pattern). Audit 2026-06-24: api_football canonical
     FIXTURES are **0 captured for 2015–2017** (35,889 all-`empty_confirmed` across 76 MVP leagues that demonstrably
     played) + 40,041 `attempted_failed` in 2018/2021/2023 — a real G2 hole. Diagnose real-tier-limit (→ honest absence,
     fix `SOURCE_COVERAGE_START`) vs backfill-bug (→ scoped `--force` re-run) BEFORE trusting any sports coverage
     number.

---

## 4. Mechanism map (where each piece lives)

- **Daily snapshot capture** (the part that pulls in NEW instruments each day) →
  `instrument_availability/by_date/ day={D}/venue={V}/instruments.parquet`. **MUST run every day** (currently the
  `instruments-service-daily-trigger` 08:30 UTC scheduler is **PAUSED** — that is the root cause of the 06-19/20/21 gap;
  un-pausing + verifying is a G1/G2 task).
- **Lifecycle roll-up / aggregation** → `instruments-service/scripts/build_instrument_catalogue.py`, Cloud Run job
  `lifecycle-catalogue-regen-{ag}`, scheduler `0 1 * * *` (01:00 UTC daily). Output `prod/catalog.parquet`
  (available_from/available_to/MVP/universe). **G3 must verify this job runs the latest code.**
- **Instruments manifest / coverage** → `_index/availability_index.parquet` (per-(day,venue), `capture_status` +
  `instrument_count`), consolidator cron `*/1`. This feeds `compute_honest_coverage` → data-status → UI.
- **Downstream catalogue artefacts** → `instrument_catalogue_scheduler.tf` (02:00), `catalogue_regen_scheduler.tf`
  (04:30) — UAC drilldown json/md + envelope.

---

## 5. 2026-06-24 cefi baseline (ground-truth audit, read-only)

GOOD: history 2019-03-30→2026-06-23 (2,640 days); MVP tags present (157,092 / 227,576); Binance stocks/commodities
present (AAPL/TSLA/MSTR/NVDA/MSFT/GOOGL/AMZN/COIN/XAU/XAG); `compute_honest_coverage` SSOT exists.

RED (drives the G1–G3 work): **3 day-gaps 06-19/20/21 silently absent** → 99.9% is blind; **expected-universe not
materialised** for missing days; coverage is **per-(venue,day) shallow** (no depth check); **per-venue counts
non-monotonic** (1000s of day-over-day drops, unreconciled); **junk-symbol noise**; **daily-capture trigger PAUSED**.

SSOT plan: `plans/active/instruments_foundation_completeness_2026_06_24.md`. Composes with:
`availability-manifest-and-data-status.md` (expected-universe materialisation, 4-state) ·
`honest-absence-downstream- handling.md` · `data-pipeline-correctness-hard-rule.md` (no cutbacks) ·
`foundation-completion-gate-discipline.md`.

---

## 6. Cross-AG lessons borrowed from the DeFi + TradFi builds (apply to EVERY AG)

These are general — surfaced in DeFi/TradFi but they upgrade the standard for cefi/sports too.

1. **Verify the captured↔expected per-(instrument,day) KEY-OVERLAP — never raw captured count (the headline G5 rule).**
   Captured rows can climb steadily while coverage doesn't move, because captures land as **net-new cells keyed
   differently than the expected-universe seeds** (the 2026-06-24 DeFi stall: captured +700k yet overlap flat — capture
   keyed on a broad top-N pool set whose `(pool,date)` cells never coincided with the window-seeded EU). The honest G5
   signal is **`expected_unattempted` DROPS / the captured∩expected key-overlap CLIMBS**, proven by grepping actual
   captured key-tuples against the expected set — NOT `captured++`. Capture and EU-seed MUST key on the byte-identical
   atom (instrument_id form/case, venue, chain, instrument_type, date, pipeline_mode); any drift = overlap stays flat.

2. **Audit every source for SILENT CAPS — a truncating cap is a G1/G2 defect, and its missing rows are NOT empty.**
   Sources silently truncate the universe: The Graph `skip` caps at ~5000 (DeFi — high-volume days dropped lower-volume
   catalogue pools), a "top-N-by-TVL" daily snapshot, a REST page limit, a vendor free-tier window (TradFi Databento
   L1≈1y / L2-L3≈1mo). Each makes missing instruments look like genuine absence. For every source, find the cap and page
   PAST it (timestamp-cursor instead of skip; explicit instrument filter instead of top-N) so the full expected universe
   is reachable. **Banned: recording a cap-truncated cell as `NOT_ENOUGH_TVL`/`SOURCE_RETURNED_ZERO`** — that masks a
   fetch defect as honest absence.

3. **G5 "done" = the coverage metric MOVED in prod, not "job exited 0 / tests green" (the exit-0-but-empty blind
   spot).** A self-deleting backfill VM that crashes (exit 137) AND one that exits 0 having captured nothing look
   identical to an exit-code/RUNNING monitor; unit-tests-green proves the code, not that prod captures the right
   universe (DeFi: the cursor fix was green + shipped yet moved overlap by +8). The completion/verification signal MUST
   be the **semantic metric** (overlap climbed / EU dropped / depth rose), cross-checked against the run.log terminal
   `exit_code` — never inferred from "the VM is gone" or "the suite passed."

4. **A deliberate COST/ENTITLEMENT boundary is a distinct honest state, not failed/empty (TradFi billing-fail-closed).**
   Where a source charges beyond a free window, cells we deliberately don't fetch for cost are a typed
   `EXPECTED_*`/`KNOWN_SOURCE_GAP` cost-boundary in the expected-universe oracle (TradFi clips ~241k beyond-free
   Databento cells, fail-closed so we're never billed) — they are not `attempted_failed` and not silent absence. The
   oracle (§2.1) must carry this reason class so coverage honestly reflects "available but intentionally-unfetched."

5. **Genuine-empty requires PROOF the full universe was actually fetched (the keystone `FetchEvidence` gate).** Before
   any `SOURCE_RETURNED_ZERO`/`NOT_ENOUGH_TVL`, prove the source was queried completely for that cell (post cap-fix #2)
   — a pagination/universe miss must never masquerade as honest zero. This is the existing keystone gate
   (`UnprovenHonestAbsenceError`); the DeFi build nearly violated it (almost marked skip-cap-missed pools
   NOT_ENOUGH_TVL) — enforce it at every empty-write, every AG.

6. **EXPIRY is any-AG-with-dated-types, NOT tradfi-only (operator 2026-06-24).** cefi has PERPETUAL/SPOT (binary, no
   expiry) **AND FUTURE/OPTION that expire** — **Deribit options** + dated futures on Binance/Bybit/OKX are the
   canonical cefi case. So the §2.1.2 expiry-schedule oracle, the `available_to = venue-truth-expiry` rule (§7.3), and
   the day-to-day **"every active-drop is an EXPLAINED delisting/expiry"** check (§1.2) apply to **cefi's dated
   instruments exactly as to tradfi**. defi's analog is the per-date TVL threshold. Only perps/spot are binary-listing →
   the expiry/listing-rule registry (§2.1) is **shared cefi+tradfi**, not tradfi-scoped. The day-to-day check therefore
   **depends on venue-truth `available_to` (§7.3)** — without real expiry dates you cannot tell a legitimate roll from a
   capture gap, so a naive day-to-day HWM (defi's `_enforce_defi_monotonicity`, "never drops") is **wrong** for any AG
   with dated instruments.

---

## 7. TradFi (and cefi-dated) nuances the 24/7 venues don't have the same way (operator 2026-06-24)

### 7.1 Billable-venue guard — enumerated venues MUST equal the subscribed source set (HARD)

The venues we ENUMERATE must equal what we're licensed to source: tradfi = the Databento allowlist
`{GLBX.MDP3, DBEQ.BASIC, XCBF.PITCH}` + yahoo `{KRX, FX}`. A venue enumerated but NOT in the allowlist is a G1 defect on
**two** counts — a **billing risk** (querying a non-subscribed dataset is metered/4xx) AND **junk coverage**. **Audit
2026-06-24:** `_DATASET_TO_VENUE` still maps `IFEU.IMPACT`/`IFUS.IMPACT` → **ICE** though ICE is not billable — count
collapsed **8,856 → 1**. Enumeration MUST gate on the SAME allowlist as market-data
(`assert_databento_request_allowed`). The §1.5 noise guard extends from junk **symbols** to junk **venues**.

### 7.2 Per-venue trading calendars + sessions are MANDATORY and FAIL-CLOSED (HARD)

A closed day is recorded **honest-empty, never carried-forward, never silently absent**:
`is_non_trading_day(venue, date)` → `empty_confirmed` + `EXPECTED_HOLIDAY`/`EXPECTED_WEEKEND` (per-venue); the
instrument's holiday-viability is carried by its **lifecycle** (`available_to=None`), NOT a synthetic copied snapshot.
Market open/close + half-days live in `session_times.py`/`venue_session_hours.py`/`half_day_sessions.py`. **Two defects
(audit 2026-06-24):** (a) `is_non_trading_day` **FAILS-OPEN** for unknown venues ("unknown ⇒ 24/7") → **KRX is in NONE
of the calendar/session SSOTs** → treated 24/7 → Korean holidays (Seollal/Chuseok) mis-handled (Yahoo returns nothing →
`attempted_failed`/false gap instead of `EXPECTED_HOLIDAY`); **fix = fail-CLOSED** (an undeclared tradfi venue is a G1
config error). (b) **FX is the legit 24/7 exception** (Yahoo `KRWUSD=X`, conversion-only) but must be **DECLARED** 24/7,
not defaulted — the default is right for FX by accident and wrong for KRX. So: `FX=24/7`, `KRX=Korea Exchange`, US
venues = NYSE/CME calendars, all explicit.

### 7.3 `available_to` (delisting/expiry) = venue-truth + per-venue trading-day-aware (dual of §2.1 genesis)

The catalogue gets `available_to` wrong **two** ways (applies to ANY AG with delisting/expiry incl. cefi dated): (A)
**last-seen, not venue-truth** — it sets `available_to = last day seen in our snapshots`
(`build_instrument_catalogue.py` L476/L684) → a capture gap / tail-holiday = **false early delisting** — even though for
dated instruments we ALREADY derive the real expiry (`futures_factory.py` from Databento `definition.expiration`).
**Fix:** `available_to` = venue-truth (futures/options → contract `expiry`/`last_trading_date`; equities → venue
delisting; last-seen only a labelled fallback). (B) **`latest_day = max(all_days)` is GLOBAL across venues** → a lagging
venue gets ALL its actives stamped delisted. **Live:** KRX last-captured `06-23`, CME `06-24` ⇒ every KRX stock
`available_to=06-23` = **falsely DELISTED**; same on any divergent-calendar day (US holiday where KRX trades). **Fix:**
`latest_day` **per-venue + trading-day-aware** — active iff present on its own venue's latest TRADING day. (Running the
regen before this fix bakes false KRX delistings — the audit pause was correct.)

### 7.4 KNOWING the cumulative HISTORICALLY = Tier-B, not self-comparison (operator 2026-06-24)

§1.2's cumulative-monotonic computed over OUR snapshots is a **Tier-A guard only** — **circular** for completeness (a
missing/shallow day understates the cumulative; a later fuller capture looks like "growth"). To KNOW it: **Tier-B
external truth** (§2.1) — Databento `definition` is **point-in-time** (re-query day D = the venue's real universe that
day), so a complete daily backfill IS the truth, cross-checked against the encoded **expiry/listing rules** (a contract
the rules say existed but isn't in the snapshot is a provable gap); yahoo venues (KRX/FX) = a small **static
genesis-anchored** set. "Cumulative grows in our data" is necessary-but-not-sufficient.

### 7.5 Remediation re-fetch trigger — NOT blanket `--force`, NOT just "unexpected-missing" (HARD)

`--force` re-fetches good shards (waste + billing + slow); plain skip-if-exists **misses SHALLOW captures** (a day
`captured` with 41 of thousands is skipped). Correct: **(a)** materialise the expected-universe (silent-absent → EU;
each shard gets an **expected depth** from the §2.1 oracle); **(b)** re-fetch ONLY
`{missing/EU, attempted_failed, captured-but-instrument_count < expected_depth}`. Depth-aware — _requires_ the depth
oracle. (Drilldown-correctness = §2.3 + the §6.1 key-overlap rule.)

---

## 8. Retirement completeness — "shouldn't exist" is NOT fixed by code alone (HARD RULE, every AG)

Stopping enumeration prevents NEW bad data; existing GCS snapshots + manifest rows persist and keep polluting catalogue/
coverage/`/data-status`/UI. **Plans-Run-To-Completion applies to REMOVALS too.** A retired thing (ICE; VIX cash index;
the cefi-domain equity-perp singles; CBOE SPOT_PAIRs) is done only when **all four** are clean: **(1) code** — delete
the path **+ a documented exclusion marker** (so it isn't re-added); **(2) GCS** — delete the snapshots (whole-venue =
`by_date/day=*/venue=ICE/`; row-level pollutant = filter rows out of the venue parquet, surgical); **(3) manifest** —
purge `_index/availability_index.parquet` rows (pause consolidator → snapshot → filter → resume); **(4) surfaces** —
verify gone from catalogue/`/data-status`/UI. **Live proof (2026-06-24):** the VIX cash index was deleted only in the EU
enumerator (`_is_vix_cash_index`) but the **adapter still creates it** (`YAHOO_INDICES`) → CBOE today = **5 INDEX rows**
→ manifest → catalogue → UI. Code-only = half a fix.

---

## 9. TradFi 2026-06-24 baseline (ground-truth audit)

GOOD: 7 venues incl. new **KRX** (routing + cefi-`AssetClass` crash fixed, IS `50bf1c8`); VX futures under CBOE as
`FUTURE`; honest-empty holiday model + session SSOTs for US venues; shared `compute_honest_coverage`. RED (G1–G3): **KRX
96% silently absent** (62/1,690 days, 60 `attempted_failed` pre-fix) + **no Korea calendar/sessions** (24/7); **ICE
non-billable** yet enumerated (8,856→1); **CBOE polluted** (9 VX FUTURE + **91 SPOT_PAIR + 5 un-deleted INDEX**);
**equities only from 2023-04-15** (pre-2023 silently absent); NASDAQ ~41 / NYSE ~224 (shallow-or-MVP, no depth oracle);
`available_to` false-delistings (global-`latest_day` bug); verify the tradfi daily-capture trigger isn't PAUSED (the
cefi one is). FX = Yahoo `KRWUSD=X`, conversion-only, legit 24/7. SSOT plan
`plans/active/instruments_foundation_completeness_2026_06_24.md` is **referenced by §5 but does not exist yet — needs
writing.**
