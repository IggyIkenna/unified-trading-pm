---
doc_type: audit-result
title: "Data-pipeline reconciliation — cefi (2026-08-20), raw-tick layer, Tier-1 only"
summary: >-
  Scheduled daily cefi spot-check (cefi_reconciliation_auditor role, dispatch agt-9c12a6, slot 27). Phase 0: the
  market-data-tick-cefi consolidator P0 (`manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md`, stuck
  phantom lock) is CONFIRMED FULLY RESOLVED — canonical index fresh (~20min old at probe, generation advanced past
  last night's 22:16Z recovery), stall streak 0 (was 183), latest run a genuine small incremental merge
  (168,125 shards scanned, 30 changed, `verdict=produced`). instruments-store-cefi healthy as every prior run. AWS
  mirrors empty as every prior run. §3f census re-measured fresh (manifest advanced since the 08-18/08-19 freeze) and,
  for the first time, cross-checked against deployment-api's `_ACCEPTED_EXCEPTIONS` dict (a suppression mechanism
  missing from this skill's own documented list until this run) — 3 of 7 raw venue "drift" values
  (`BYBIT-FUTURES`/`OKEX-FUTURES`/`CRYPTOFACILITIES`) and both `instrument_type` bundle-grain values
  (`futures_chain`/`options_chain`) are operator-accepted aliases, not fresh findings; codex + the skill file corrected
  in the same turn. The C2a casing residual (`perpetual`/`future`/`spot_pair`, migration_pending, suppressed per the
  D1 ruling) is corroborated BYTE-IDENTICAL to the tracked `cefi_instrument_type_casing_active_writer_regression_
  2026_08_17.md` issue's 2026-08-17 post-fix baseline — confirms the shipped writer fix (`c07cc70e93`) is holding
  with zero regrowth in 3 days. Incidental finding while cross-referencing that issue: its historical-backlog cleanup
  dry-run VM (`canonical-migration-cefi-itype-casing-apply-20260818-012605`) died silently ~46h ago (same freeze
  pattern as its predecessor, undocumented) — appended to that issue's Progress Log, not re-diagnosed here
  (VM-ops forensics is out of this role's Tier-1 scope). Honest-coverage: no fresher rollup than 08-19's exists yet
  at probe time (00:1xZ, before the job's ~00:4xZ cadence) — re-verified the SAME formula against the same file,
  matches exactly. No live-infra code fix needed this run (the one P0 candidate was already fixed by a prior session);
  2 codex/skill doc fixes + 1 issue-doc Progress Log append shipped instead.
status: pass
nature: record
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, market-tick-data-service, deployment-api]
scope: [engineer, admin]
tags:
  [
    reconciliation,
    canonicalisation,
    census,
    cefi,
    honest-coverage,
    consolidator-p0-resolved,
    accepted-exceptions-suppression-gap-fixed,
    bybit-futures-selfheal-growth,
    casing-writer-fix-holding,
    casing-apply-vm-stalled-again,
    depth-of-book-10-carried,
    binance-delivery-carried,
    bare-okx-carried,
  ]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    reconciliation-census-and-compute-tiers,
    honest-coverage-model,
    manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19,
    cefi_instrument_type_casing_active_writer_regression_2026_08_17,
    data_pipeline_reconciliation_cefi_2026_08_19,
  ]
created: 2026-08-20
resulting_plan:
lib_version: "market-tick-data-service@HEAD (slot 27, venv rebuilt this run via `uv sync` after the pre-existing
  .venv was found missing mid-session — see §0), unified-api-contracts@HEAD, deployment-api@HEAD (read-only import
  of `_distinct_values.py`'s accepted-exception registries; no service code changed)"
doc_versions_checked:
audited_scope:
  "asset_group=cefi, layer=raw-tick, PROD (-prd-) buckets only, read-only, Phase 0 + census (Tier-1) +
  honest-coverage verification per the cefi_reconciliation_auditor role (subset of /data-pipeline-reconciliation) —
  daily scheduled spot-check, not a full campaign. Fifth consecutive daily run (prior: 2026-08-16, 08-17, 08-18,
  08-19)."
date: 2026-08-20
auditor: "cefi_reconciliation_auditor (scheduled role, slot 27, dispatch agt-9c12a6)"
parent_epic: security_and_cross_cutting_master
severity: P2
skill: data-pipeline-reconciliation
run_date: 2026-08-20
generated_at: 2026-08-20T00:35:00+00:00
---

# Data-pipeline reconciliation — cefi (2026-08-20), raw-tick layer, Tier-1 only

**Read-only against prod data this run** — no GCS writes, no manifest writes, no deletes, no VM launches. Two small
codex/skill doc corrections shipped (a suppression-mechanism gap this run's own census tripped over) plus one
Progress Log append to an existing tracked issue (an incidental live-state finding). Daily scheduled
`cefi_reconciliation_auditor` spot-check: Phase 0 (reachability + freshness) + the §3f distinct-value census +
honest-coverage formula/freshness verification. Fifth consecutive daily run since the 2026-08-16 restart
(predecessors: 2026-08-16, 08-17, 08-18, 08-19).

**§0 — environment note.** MTDS's `.venv` was found missing at session start (present at boot per the slot's own
liveness check, gone by the time this run's Phase-0 script executed — no diagnosis attempted, git status in the repo
was clean throughout so no tracked content was at risk; rebuilt via `uv sync`, no `pip install`). All reads below ran
against the rebuilt venv.

## 0. Phase-0 reachability + freshness

| bucket | reachable | consolidator lock | canonical `availability_index.parquet` | verdict |
| --- | --- | --- | --- | --- |
| `market-data-tick-cefi-prd-central-element-323112` | yes | held ~8min at probe (00:01:19Z start, instance `1-19fe7807`) — a normal in-progress hourly cycle, not stale | generation `1787183606908050`, `2026-08-19T23:53:26.92Z` (**~20min old at probe**), 480,922,217 bytes | **HEALTHY — consolidator P0 fully resolved** |
| `instruments-store-cefi-prd-central-element-323112` | yes | not present (never locked, as every prior run) | generation `1787184072576382`, `2026-08-20T00:01:12.59Z` (fresh) | healthy, consistent with every prior run |

**AWS cross-check**: both mirror buckets (`market-data-tick-cefi-prd-427895769566`,
`instruments-store-cefi-prd-427895769566`) reachable, `top_level_prefixes=0` — unchanged from every prior run.

### Consolidator P0 — CONFIRMED FULLY RESOLVED (independent live re-check, not a re-file)

`manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md` (filed 08-19T19:5xZ, escalated to P0, dispatched)
was root-caused and recovered **overnight, before this run started**: a marker-restore recovery executed
2026-08-19T22:2xZ broke the doomed-full-merge/timeout/orphan-lock wedge loop, the canonical advanced
`1787019237694916 → 1787177809821805`, and a code fix (`unified-trading-library@af783d92e4`, the
`_UNPROVABLE_MERGE_MAX_SHARDS` cutoff) plus a watchdog fix (`@53abdf72f3`) shipped to prevent recurrence. **This run's
independent Phase-0 read corroborates the recovery held**, one probe cycle further on:

- `_index/latest.json`: `last_run_at=2026-08-19T23:53:45.53Z`, `success=true`, `verdict="produced"`,
  `shards_scanned=168125`, `shards_changed=30`, `rows_in=30,810,710`, `rows_out=30,749,403`, `dedup_dropped=61,307`,
  `incremental=true`, `no_op=false`, `error_reason=""` — a genuinely small, healthy incremental cycle, not the doomed
  full-merge shape.
- `_index/consolidator_stall_state.json`: **`streak=0`** (`baseline_shards=168125`) — down from the 08-19 report's
  escalated 183. Zero stalled cycles since the recovery.
- `_index/consolidator.lock` at probe time (`00:09:34Z`): `started_at=2026-08-20T00:01:19.18Z`,
  `instance=1-19fe7807` — **~8 minutes old**, consistent with the normal hourly `0 * * * *` schedule firing at 00:00
  and still mid-cycle; nowhere near the 9000s TTL. Not flagged as a repeat of the incident.
- The ONE remaining open todo on that issue doc (`[INFRA] P2. Rebuild the market-tick-data-service:latest image so
  both shipped fixes reach their running Cloud Run jobs`) is unchanged — not re-verified this run, correctly still
  tracked there, not blocking (the marker-restore recovery already fixed the LIVE condition; the image rebuild only
  matters for defense-in-depth against a FUTURE recurrence).

`phantom_audit_latest.json`: `phantom_count=0`, `generated_at=2026-07-27T17:38:18Z` — **now 24 days stale** (was 23
on 08-19), carried, escalating by 1 day, zero remediation for 3+ weeks.

`_index/reprobe_audit_latest.json`: `generated_at=2026-08-19T09:01:30.9Z`, `day=2026-08-19` — **today's has not run
yet** (probe was 00:1xZ, well before the confirmed ~09:00Z daily cadence; this is timing, not staleness — this run's
own dispatch fired much earlier in the day than the 08-16..08-19 predecessors, which is why several daily artifacts
below show as "not yet regenerated today" rather than a fresh problem).

`instruments-store-cefi` still has **no** `phantom_audit_latest.json` / `reprobe_audit_latest.json` (both 404,
confirmed via direct read) — standing declared coverage gap, unchanged.

## 1. Census — venue axis (fresh re-measure; manifest has moved since the 08-18/08-19 freeze)

The consolidated manifest advanced from the frozen `1787019237694916` (08-18T02:13:57Z) through the recovery merge to
`1787183606908050` (08-19T23:53:26.92Z) — this run's census is a genuine fresh read (30,749,403 rows, matching
`latest.json`'s own `rows_out` exactly — a live consistency check, not a cached number), not carried.

**Suppression correction this run (methodology fix, not a data change):** this skill's own documented suppression
list (SKILL.md §3f, and its codex SSOT `reconciliation-census-and-compute-tiers.md` §1.5) named four suppressions
(C2a casing / decision-D lending / `batch_massive` / sports blank sentinels) but **omitted** deployment-api
`_distinct_values.py`'s `_ACCEPTED_EXCEPTIONS` dict — a real, live, per-`(axis, asset_group)` suppression mechanism.
Checked directly against the source this run (`unified-api-contracts/registry/market_data_categories.py:753-785`,
`deployment-api/routes/data_status/_distinct_values.py:248-299`) and found it applies to **3 of the 7 raw venue
values below** and **both** raw `instrument_type` bundle-grain values (§2). Both docs corrected in this same turn
(`unified-trading-pm@<pending>`) — prior daily reports (08-16 through 08-19) carried these 3 venue values + both
bundle-grain values as open/candidate findings without checking this dict; they were already accepted.

- **C − M (orphaned declarations)**: still **empty** — all 25 UAC-declared cefi venues have manifest presence.
- **M − C, suppressed (operator-accepted dialect alias, `CEFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES`)**:
  - `BYBIT-FUTURES` (**25,654**, 100% `empty_confirmed` — up sharply from 08-19's carried 10,268; explained below,
    not a new problem) — folds to canonical `BYBIT`.
  - `OKEX-FUTURES` (36, 100% `empty_confirmed`, unchanged) — folds to canonical `OKX-FUTURES`.
  - `CRYPTOFACILITIES` (10, 100% `empty_confirmed`, unchanged) — folds to canonical `KRAKEN-FUTURES`.
- **M − C, genuine open findings (4, unchanged in count from every prior run — carried)**:
  - `OKX` bare (5,225, 100% `attempted_failed`) — identical to every prior run since the origin fix; historical
    residue from the already-shipped bare-OKX writer fix, not actively growing.
  - `BINANCE-DELIVERY` (4,838: `empty_confirmed=4,255` + `attempted_failed=578` + `captured=5`) — byte-identical to
    every prior run.
  - `KALSHI_PERP` (2, 100% `attempted_failed`) — byte-identical. Looks like an underscore/hyphen dialect of canonical
    `KALSHI-PERP` (28,596 rows, real) but is **not** in `CEFI_VENUE_FOLD` — genuinely unaccepted, not a false
    negative of the new suppression check.
  - `OKX-OPTIONS` (2, 100% `attempted_failed`) — byte-identical.

**Why `BYBIT-FUTURES` more than doubled (10,268 → 25,654) — not a new bug.** This is the accepted dialect alias for
an actively self-healing writer (per the 08-19 report's "bybit-futures-selfheal-stable" tag): every OTHER venue in
this list stayed byte-identical to 08-19's frozen numbers (confirming today's manifest genuinely re-measured, not
guessed), while only `BYBIT-FUTURES` grew — consistent with rows this writer kept producing DURING the 08-18/08-19
consolidator outage (invisible to the frozen canonical read) landing all at once when the recovery merge caught up.
Since it is an accepted alias, the growth is not itself reportable as a finding; noted here only so the jump isn't
mistaken for new drift.

## 2. Census — instrument_type + data_type + chain axes

- **`instrument_type` bundle-grain, suppressed (`CHAIN_BUNDLE_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES`, permanent
  MTDS Tardis-writer bundle stamp, never a per-contract `InstrumentType` member)**: `futures_chain` (175,484:
  `empty_confirmed=121,386` + `expected_unattempted=43,867` + `attempted_failed=10,231`) and `options_chain` (36,382:
  `empty_confirmed=24,394` + `expected_unattempted=8,580` + `attempted_failed=3,408`) — both grew modestly from the
  08-17-measured 173,043/36,329 (normal day-over-day bundle-row accumulation, not a defect).
- **`instrument_type` C2a casing (migration_pending, suppressed per the D1 ruling — target UPPERCASE, column
  mixed-case during the migration window)**: `perpetual`=38,083, `future`=1,191, `spot_pair`=12, `index`=3,910.
  **Corroboration against the tracked writer-regression issue**
  (`cefi_instrument_type_casing_active_writer_regression_2026_08_17.md`): `perpetual`/`future`/`spot_pair` are
  **byte-identical** to that issue's 2026-08-17 05:44Z post-fix measurement (sum 39,286, exact match) — **confirms
  the shipped writer fix (`market-tick-data-service@c07cc70e93`) is holding, zero regrowth in 3 days.** `index`
  (3,910) is separately tracked in that same issue as "unclassified, not a casing variant" (DERIBIT
  `volatility_index` registry gap, carried P4 here, unchanged from 08-19). See §4 for an incidental finding on that
  issue's OWN still-open historical-backlog `--apply` VM.
- **`data_type` (7 distinct values outside canonical vocab — no cefi entry in `_ACCEPTED_EXCEPTIONS`, all genuine,
  open, carried findings)**:
  - `depth_of_book_10` (56,178: `empty_confirmed=36,412` + `captured=19,689` + `attempted_failed=77`) — up from
    08-19's carried 39,120 (11,914 captured). Same explanation as `BYBIT-FUTURES` above: this data_type is produced
    by `bybit_futures_book_ticker_ws.py` (BYBIT-FUTURES's own self-heal writer), so the outage-catch-up growth is
    the same event, not two separate anomalies.
  - `perp_daily_ctx` (10, all `captured`) — up from 7, consistent with steady ~1/day accumulation (carried P4,
    "confirm in-scope or expected-pilot").
  - `ohlcv_{15m,15s,1d,1h,5m}` (2 each, 10 total, all `captured`) — byte-identical to every prior run.
- **`chain`**: 100% blank — the 2026-07-28 chain-axis heal holds, unchanged.
- **`C − M` (instrument_type, case-insensitive):** 26 `InstrumentType` enum members absent from the cefi manifest —
  **not a finding**: these are OTHER asset_groups' types (`EQUITY`/`BOND`/`LENDING`/`POOL`/`STAKING`/…) that cefi
  never claims; `InstrumentType` is a cross-asset-group enum, and cefi correctly uses only its own 6
  (`PERPETUAL`/`SPOT_PAIR`/`FUTURE`/`OPTION`/`COMBO`/`INDEX`, case-insensitively) plus the 2 accepted bundle-grain
  stamps above. Listed in the JSON sibling for completeness, not reproduced here as a table.

## 3. Honest-coverage — no fresher rollup than 08-19's exists yet at probe time (expected, not staleness)

- Probed `2026-08-20/coverage.json` — **not found** (probe was 00:1xZ; the job's own cadence, per the 08-19 report's
  own timing note, is ~00:4x-00:49Z daily — today's run had not fired yet).
- Freshest available: **`2026-08-19/coverage.json`** (`generated_at=2026-08-19T00:43:16Z`, unchanged from what the
  08-19 report itself already verified — this is the SAME file, not a new one). `by_asset_group.cefi`:
  `captured=9,866,487`, `empty_confirmed=6,392,460`, `attempted_failed=892,679`, `expected_unattempted=10,894,199`,
  `total=28,045,825`, published `coverage_pct=45.57`.
- **Formula re-verified**: `9,866,487 / (9,866,487 + 892,679 + 10,894,199) = 9,866,487 / 21,653,365 = 45.5656…%` —
  matches published `45.57` exactly. **No formula drift.**
- `instrument_gates_download=true` → lower bound. `layer1_completeness_pct=94.52` (unchanged, matches the
  2026-08-17-certified baseline). `denominator_complete=false` / `denominator_status="INCOMPLETE"` (unchanged, same
  4 real Layer-1 holes as every prior certified read: `BITGET-FUTURES/future/{book_snapshot_5,derivative_ticker}`,
  `OKX-FUTURES/perpetual/{book_snapshot_5,derivative_ticker}`).
- Rollup age at probe: **~23.6h** (approaching but not exceeding the ~24h daily cadence) — not flagged stale; expect
  a fresh `2026-08-20` file within the hour of this report if re-checked later today.

## 4. Incidental finding — the casing-fix issue's own historical-backlog VM stalled again (not re-diagnosed here)

While corroborating §2's casing numbers against `cefi_instrument_type_casing_active_writer_regression_2026_08_17.md`,
found its still-open todo ("review the 2026-08-18 dry-run's disposition, then launch the full `--apply`") has been
sitting unreviewed for ~2 days. Checked live (cheap, read-only): `gcloud compute instances describe
canonical-migration-cefi-itype-casing-apply-20260818-012605` → 404 (VM gone); its `run.log` is a flat run of
`PIPELINE_HEARTBEAT` lines ending abruptly at `2026-08-18T01:59:32Z` (last_modified `02:01:40.949Z`, **~46h frozen**
at check time) — no `Grand total` completion line, no error, no shutdown marker. **This is the identical freeze
signature as the FIRST dry-run VM** (`...-20260817-130229`, independently diagnosed in that issue doc as an
~85-minute total kernel/systemd-level freeze followed by a real zombie-watchdog kill) — undocumented until this run.
**Appended to that issue's own Progress Log** (not re-diagnosed, not relaunched, not `--apply`'d — genuinely
VM-scale forensics/ops work, out of this Tier-1 read-only role's scope; the issue's own todo chain already names the
next step). Flagged here only so this daily report doesn't silently omit a live-state fact discovered along the way.

## 5. What this run does NOT cover (declared, per the role's Tier-1 scope)

- No machine-oracle path-structure sweep, no id-form/schema Tier-1 sampled check or Tier-2 VM validation, no
  orphan-object sweep / delete suggestions — never this role.
- No GCS-side delimiter descent (G vs C / M vs G) this cycle — the manifest-side (M vs C) census plus the clean C-M
  orphan check gave sufficient Tier-1 signal; consistent with every prior daily run's scope.
- Did not diagnose or relaunch the stalled casing-apply VM (§4) — out of scope, correctly deferred to its own issue.

## 6. Fixes shipped this run (docs only — no service/infra code changed)

- **`unified-trading-pm/codex/02-data/reconciliation-census-and-compute-tiers.md`** §1.5 — added the missing
  `_ACCEPTED_EXCEPTIONS` suppression bullet (§1 above).
- **`unified-trading-pm/cursor-configs/skills/data-pipeline-reconciliation/SKILL.md`** §3f — same addition, kept in
  sync with its codex SSOT.
- **`unified-trading-pm/plans/archive/issues/cefi_instrument_type_casing_active_writer_regression_2026_08_17.md`** —
  Progress Log entry appended (§4's finding); no checkbox flipped (the work itself is not done).

## 7. Todos

- [ ] [DATA] P2. **`BINANCE-DELIVERY` venue drift (4,838 rows, carried, byte-identical for 5+ consecutive days)** —
      still needs the launcher/registry grep to confirm which config still probes it. Repo: market-tick-data-service
      / unified-api-contracts.
- [ ] [DATA] P2. **`depth_of_book_10` data_type registry gap (56,178 rows, 19,689 `captured`, carried, self-heal
      durable — grew this cycle via the same BYBIT-FUTURES outage-catchup as §1, not a new issue)** — produced by
      `bybit_futures_book_ticker_ws.py`, undeclared in `DATA_TYPES_BY_ASSET_GROUP["cefi"]`. Decide add-vs-document;
      an addition needs downstream consumers checked in the same change. Repo: unified-api-contracts.
- [ ] [INFRA] P2. **Follow up on `canonical-migration-cefi-itype-casing-apply-20260818-012605`'s silent 2nd-time
      freeze** (§4) — needs VM-ops forensics (serial console + zombie-watchdog Cloud Logging, same method as the
      130229 precedent) and a relaunch on a fresh VM; tracked on
      `cefi_instrument_type_casing_active_writer_regression_2026_08_17.md`'s own todo chain, this is a pointer, not
      a duplicate. Repo: market-tick-data-service / deployment-service.
- [ ] [INFRA] P3. **`phantom_audit` for cefi now 24 days stale** (was 23 on 08-19, zero remediation for 3+ weeks) —
      carried, escalating by 1 day. Repo: instruments-service.
- [ ] [DATA] P4. **`instrument_type=index` (3,910 rows, DERIBIT/volatility_index, carried, byte-identical)** — still
      undeclared in any cefi registry. Repo: unified-api-contracts.
- [ ] [DIAG] P4. **`perp_daily_ctx` data_type (10 `captured` rows, carried, +3 since 08-19 — steady accumulation)** —
      confirm in-scope or expected-pilot. Repo: unified-api-contracts.

**Resolved / closed this run (not carried forward as open findings):** the market-data-tick-cefi consolidator P0
(§0 — independently confirmed healthy, already closed by last night's recovery, not this run's own fix); 3 of 7
venue-axis census findings and both instrument_type bundle-grain values (§1-2 — confirmed operator-accepted, were
never genuine open findings, a report-methodology correction not a data change); `CRYPTOFACILITIES`/`OKEX-FUTURES`'s
prior "candidate for the accepted-exception list" P3 todo (08-19 report §6) — resolved by discovering they were
**already** on it.

## Progress Log

- **cefi_reconciliation_auditor 2026-08-20** [dispatch agt-9c12a6, slot 27]: Phase 0 + freshness + census +
  honest-coverage verification complete, read-only against prod data. Headline: the market-data-tick-cefi
  consolidator P0 filed last night is CONFIRMED FULLY RESOLVED (independent live re-check: stall streak 0, fresh
  canonical, healthy small incremental cycles). Found and fixed a suppression-mechanism gap in this skill's own
  documented census methodology (`_ACCEPTED_EXCEPTIONS` dict was never checked) — corrected `SKILL.md` +
  its codex SSOT in the same turn; re-classified 3 of 7 venue findings and both instrument_type bundle-grain
  findings as already-accepted, not open. Corroborated the tracked cefi instrument_type casing writer-fix is
  holding (byte-identical residual to the 08-17 post-fix baseline, 3 days zero regrowth). Incidentally found that
  issue's own historical-backlog dry-run VM died silently a second time (~46h stale, same freeze signature as its
  predecessor) — appended to that issue's Progress Log rather than re-diagnosed (out of this role's Tier-1 scope).
  No fresher honest-coverage rollup than 08-19's existed at probe time (pre-cadence timing, not staleness) —
  re-verified the same formula against the same file. No live-infra code fix needed (nothing found broken that
  wasn't already fixed or already tracked); 2 codex/skill doc fixes + 1 issue-doc Progress Log append shipped.
