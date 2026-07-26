---
doc_type: issue
title:
  DP_CATALOG_NOT_RUNNING fired for sports + prediction (25.7h/25.8h stale) — two UNRELATED root causes, both
  pre-existing, NOT caused by the same-session tradfi corp-actions fix
summary:
  'Two CRITICAL `DP_CATALOG_NOT_RUNNING` (DP-CATALOG-001) alerts fired 2026-07-15 ~03:47 local for sports
  (`instruments-store-sports-prd-…/prod/catalog.parquet`, 25.7h stale) and prediction
  (`instruments-store-pred-prd-…/prod/catalog.parquet`, 25.8h stale). Investigated as a regression-suspect against the
  same-session instruments-service commit `03f71c81a` (tradfi corp-actions MTDS-manifest exclusion) — CLEARED: that
  commit touches only `enumerate_expected_universe.py` (the expected-universe/manifest-seeding script, writes
  `_index/availability_index.parquet`), never `build_instrument_catalogue.py` (the actual `prod/catalog.parquet` writer
  these alerts probe) — a structurally different script/artifact — and its edit is `elif asset_group ==
  "tradfi":"`-scoped in both call sites, never touching the sports/prediction branches. Root causes (confirmed via live
  Cloud Run Job logs, both PRE-DATE the 03f71c81a commit landing at 2026-07-15T02:21:54Z): **sports** —
  `lifecycle-catalogue-regen-sports`''s monotonic guard REJECTED a same-day roll-up (27,210 rows < previous 27,216) as
  `CATALOGUE_SHRINK_BLOCKED`, correctly refusing to overwrite the prod catalogue with a smaller row count (exit 1,
  01:00:59 UTC 07-15 — before the commit existed). **prediction** — `lifecycle-catalogue-regen-prediction` has been
  SIGKILLed (signal 9, consistent with OOM against its 4Gi Cloud Run memory limit) at the monotonic-guard/promote-write
  stage on 3 consecutive days (07-13, 07-14, 07-15), first failure ~40h before the commit landed.'
nature: issue
asset_group: [sports, prediction, cefi, defi]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer, admin]
tags:
  [
    catalog,
    catalogue,
    monotonic-guard,
    oom,
    cloud-run-job,
    monitoring,
    data-pipeline,
    sports,
    prediction,
    cefi,
    defi,
    duplicate-merge-key,
    incremental-merge,
  ]
related:
  [
    codex/05-infrastructure/data-pipeline-alerts.registry.yaml,
    /codex/02-data/instruments-foundation-and-catalogue-completeness.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    plans/active/issues/cefi_monotonicity_guard_alerting_and_dark_venues_2026_07_07.md,
    plans/archive/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md,
    plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
    plans/active/issues/utl_uac_skew_fleet_audit_2026_07_15.md,
  ]
created: 2026-07-15
parent_epic: instruments_master
priority: P1
source:
  [
    "operator report: CRITICAL DP_CATALOG_NOT_RUNNING x2 (sports, prediction) at 2026-07-15 ~03:47",
    "Group-C Cloud Run job-failure triage, 2026-07-16 (utl_uac_skew_fleet_audit_2026_07_15.md follow-up)",
  ]
status: open
assigned_vm:
resolved_by:
  [
    "instruments-service@24f84e86 (sports)",
    "deployment-service@6bfa284 (prediction)",
    "re-verified live 2026-07-23 -- cefi addendum STILL OPEN, see RE-TRIAGE",
  ]
locked_by:
locked_since:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-16
---

## Regression check against same-session instruments-service@03f71c81a — CLEARED

Commit `03f71c81ad055eea1f55f1cddc4607a40ac5b5ba` (2026-07-15T03:21:54+01:00 = **02:21:54 UTC**) added
`_TRADFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES` + `_tradfi_mtds_tick_manifest_data_types()` to
`instruments-service/scripts/enumerate_expected_universe.py`, wired into two `elif asset_group == "tradfi":` branches
(`enumerate_v2()` and `main()`). Two independent lines of evidence clear it:

1. **Wrong artifact/script entirely.** `enumerate_expected_universe.py` READS a catalog parquet (via `--catalog-path`)
   and WRITES `_index/availability_index.parquet` + `_index/expected_universe_ranges.parquet` (the
   expected-universe/manifest-seeding artifact). The alert probes `prod/catalog.parquet` — that file is written by a
   DIFFERENT script, `build_instrument_catalogue.py` (confirmed via
   `gcloud run jobs describe lifecycle-catalogue-regen-{sports,prediction}`: container args are
   `/app/instruments-service/scripts/build_instrument_catalogue.py --asset-group {sports,prediction} ...`). The two
   scripts are architecturally separate; the tradfi fix never touches `build_instrument_catalogue.py`.
2. **Even if it were the same script, the edit is tradfi-scoped.** Both call sites are `elif asset_group == "tradfi":`
   branches; sports hits its own pre-existing `elif asset_group == "sports":` branch (`_sports_data_types()`, unchanged)
   and prediction falls through the unchanged generic `else`. No shared helper was touched.
3. **Timing precludes causation regardless.** Both failing Cloud Run executions started BEFORE the commit landed: sports
   `lifecycle-catalogue-regen-sports-ffgl4` started 2026-07-15T01:00:15Z; prediction
   `lifecycle-catalogue-regen-prediction-7d4sz` started 2026-07-15T01:00:13Z — both ~1h20m before the commit's 02:21:54Z
   landing, and the prediction failure streak's FIRST occurrence (07-13, execution `jlwmj`) was 2026-07-13T01:00:07Z,
   ~49h before the commit existed.

## Actual root causes (confirmed via live Cloud Run Job log reads)

### Sports — `CATALOGUE_SHRINK_BLOCKED`, monotonic guard working as designed

`lifecycle-catalogue-regen-sports` (Cloud Run Job, `asia-northeast1`, daily `0 1 * * *` UTC) rolled up 27,210 sports
catalogue rows from `sports_reference/by_date/` — 6 rows FEWER than the current promoted catalogue (27,216). The
monotonic guard (`build_instrument_catalogue.py`'s promote-write step) correctly REJECTED the write:
`Monotonic guard: new=27210 current=27216 decision=REJECT (shrink_blocked)` →
`CATALOGUE_SHRINK_BLOCKED: new=27210 < current=27216 — keeping previous good catalogue ... (pass --allow-catalogue-shrink to override for a legitimate corrective shrink)`
→ `exit_code=1`. This is the guard doing its job (per DP-CATALOG-002's own registry entry,
`detector: promote_catalogue/evaluate_monotonic_guard`) — the last GOOD catalogue (2026-07-14T01:06:00Z, 27,216 rows)
stayed live, but the job's exit(1) means the daily refresh never advances, so DP-CATALOG-001 (staleness) fires once the
gap crosses 24h. **Needs an operator call**: is the 6-row shrink a legitimate correction (league
de-registration/retirement — this codebase has an active 24-league de-registration ruling per
`enumerate_expected_universe.py`'s `_SPORTS_LEAGUE_ID_SENTINELS`/UAC `LEAGUE_REGISTRY` gate) that should be re-run with
`--allow-catalogue-shrink`, or a genuine by_date data regression that needs investigation first?

Secondary finding (non-blocking but worth fixing): the job's own `CATALOGUE_SHRINK_BLOCKED` structured-event upload to
the `central-element-323112-events` bucket 403s (`lifecycle-catalogue-regen@…iam.gserviceaccount.com` lacks
`storage.objects.create` on that bucket) — the failure reason is visible in Cloud Logging but never reaches the
structured event-log sink, degrading observability for this exact incident class.

### Prediction — SIGKILL (signal 9) at monotonic-guard/promote-write, 3 consecutive days

`lifecycle-catalogue-regen-prediction` has failed 07-13, 07-14, 07-15 (last success 07-12,
`lifecycle-catalogue-regen-prediction-vhlf2`). Each failing run reaches `[BISECT-E] monotonic-guard + promote-write`
(2,673,230 rows, MVP-tagged) and is then killed: `Container terminated on signal 9` — both retry attempts (task0, task1)
hit the identical point before the job gives up. The Cloud Run Job's resource limit is `cpu: 2, memory: 4Gi` — signal 9
immediately after MVP-tagging a 2.67M-row dataframe and before the guard/promote step completes is consistent with an
OOM kill, not an application exception (no traceback, no `CATALOGUE_ROLLUP_FAILED` event — the process is killed
externally). `prod/catalog.parquet` for prediction is frozen at 2026-07-14T00:58:37Z / 2,673,230 rows (the last
successful promote). Needs: bump the job's memory limit (or slim the guard/promote-write step's peak memory) and re-run.

## 2026-07-15 — sports 6-row diagnosis + fix (follow-up investigation)

Dispatched to identify the EXACT 6 rows behind the sports `CATALOGUE_SHRINK_BLOCKED` (27,216→27,210) per the operator's
"investigate the 6-row diff first" decision. Reproduced the roll-up read-only against live prod GCS (downloaded the live
`prod/catalog.parquet`, re-ran `build_sports_catalogue_from_manifest` + `build_sports_fixture_team_player_catalogue`
directly) and cross-checked against live `gcloud logging read` for both `lifecycle-catalogue-regen-sports` executions.

**The exact accounting (not a simple "6 rows removed" — a 9-removed / 3-added net of -6):**

- **9 rows aged OFF** the fixture/team/player (FTP) grain's rolling window — every one of them had
  `available_from == available_to == "2025-06-09"` in the live catalogue (their ONLY ever-observed day), which is
  exactly `since_2026-07-14 = 2026-07-14 − 400d`. When `since` advanced to `2026-07-15 − 400d = 2025-06-10` on the next
  run, day `2025-06-09` fell out of the walked window entirely (confirmed via `gcloud storage ls` on
  `sports_reference/by_date/day=2025-06-09/**`: 95 ftp-entity blobs live there) and these 9 rows had no other day to
  anchor on, so they vanished from the fresh rebuild completely:
  - `BRASILEIRAO_SERIE_B:AMAZONAS_v_ATHLETIC_CLUB:20250609` (fixture)
  - `BRASILEIRAO_SERIE_B:CRICIUMA_v_VILA_NOVA:20250609` (fixture)
  - `MLS:LOS_ANGELES_FC_v_SPORTING_KANSAS_CITY:20250609` (fixture)
  - `MLS:VANCOUVER_WHITECAPS_v_SEATTLE_SOUNDERS:20250609` (fixture)
  - `SVENSKA_CUPEN:BALKAN_v_LUND:20250609` (fixture)
  - `JOHNSON_T` (player, MLS — T. Johnson, Vancouver Whitecaps, confirmed present in
    `day=2025-06-09/.../entity=injuries/league=MLS/injuries.parquet`)
  - `MARTINEZ_D` (player, MLS — D. Martinez, LA FC)
  - `ROSARIO_O` (player, MLS — O. De Rosario, Seattle Sounders)
  - `VITE_P` (player, MLS — P. Vite, Vancouver Whitecaps)
- **3 rows gained** the same run — brand-new same-day fixtures
  (`sports_reference/by_date/day=2026-07-15/.../ entity=fixtures/league=USL_CHAMPIONSHIP/fixtures.parquet`, confirmed
  downloaded + read): `USL_CHAMPIONSHIP:MIAMI_FC_v_INDY_ELEVEN:20260715`,
  `USL_CHAMPIONSHIP:LEXINGTON_v_NEW_MEXICO_UNITED:20260715`,
  `USL_CHAMPIONSHIP:SPORTING_JAX_v_PITTSBURGH_RIVERHOUNDS:20260715`.
- **Net: −9 + 3 = −6**, exactly matching the observed `27,216 → 27,210`. league_df (94 rows, manifest-derived, unrelated
  to the by_date window) was independently confirmed unchanged both days — the entire shrink lives in the FTP grain.

**Verdict: BUG, not a legitimate shrink and not transient/flaky upstream data.**

- Not legitimate: none of the 9 rows involve a de-registered league (`_sports_league_registered`/`LEAGUE_REGISTRY` gate)
  — MLS, BRASILEIRAO_SERIE_B, SVENSKA_CUPEN are all live, currently-registered leagues. Nothing was de-listed upstream;
  these fixtures/players are still real, they just aged out of an arbitrary trailing window.
- Not transient/flaky: both 07-15 job attempts (task0 `catalogue-rollup-sports-20260715T010059Z` and its automatic retry
  `…20260715T010648Z`) found the IDENTICAL 49,916 by_date blobs and produced the IDENTICAL 27,210-row result — a
  rate-limit/partial-response flake would not reproduce byte-identically twice.
- Root cause: `build_sports_fixture_team_player_catalogue`'s trailing `SPORTS_FTP_WINDOW_DAYS=400` window is recomputed
  fresh (`since = today − 400d`) on every run, and — unlike cefi/defi/tradfi/prediction, which all get
  `_merge_incremental`'s "frozen tail" (a prior-catalogue row absent from the fresh window is carried through unchanged,
  never dropped) — sports is unconditionally forced to `mode=full` with NO merge onto the previous catalogue at all
  (`"mode=incremental is a no-op for sports"` — true when that comment was written pre-2026-07-09, false since the FTP
  grain started walking by_date). An instrument whose last-observed day ages past the window's leading edge doesn't just
  get its `available_to` closed — the WHOLE ROW disappears, contradicting the module's own documented contract ("a
  cumulative, all-instruments-ever lifecycle catalogue, NOT a current snapshot" — module docstring). This is not a
  one-off: it recurs by construction every day some number of rows age out, so the monotonic guard would keep tripping
  intermittently forever until fixed.

**Fix shipped** (instruments-service@24f84e86, quickmerge-landed on `live-defi-rollout`, quality gates green 198s):
added `_merge_sports_ftp_with_frozen_tail()` to `build_instrument_catalogue.py`, which loads the previous catalogue's
FTP-grain rows (`instrument_type in {fixture, team, player}`) and merges them onto the fresh window rebuild via the SAME
generic `_merge_incremental()` engine the other asset groups already use — its default (non-prediction, non-DeFi-pool)
merge key is the bare `instrument_id`, which already IS the fixture_id/team_id/ player_id identity these rows carry, so
no sports-specific key branch was needed; its venue-presence-gated close is a natural no-op here (sports FTP rows carry
`venue=""` by design), so an aged-off row is carried through frozen (unchanged `available_from`/`available_to`) rather
than dropped. `run_rollup`'s sports branch now loads `_load_previous_catalogue(...)` and routes the FTP grain through
this helper before concatenating with the unchanged manifest-derived `league_df`. Added 2 regression tests
(`test_sports_ftp_frozen_tail_keeps_row_that_aged_off_the_window`,
`test_sports_ftp_frozen_tail_no_prev_catalogue_returns_window_only`) proving an aged-off row survives frozen and a cold
start (no previous catalogue) still works. Full `instruments-service` quality-gates.sh passed (198s, pre-existing
unrelated warnings only: `market-tick-data-service` adapter-contract baseline, basedpyright error count,
sports_reference orchestrator function-size — none touched by this change).

**Next scheduled `lifecycle-catalogue-regen-sports` run (`0 1 * * *` UTC)** should now produce a monotonically-growing
catalogue (frozen tail preserves all 9 aged-off rows + the FTP window's fresh recompute + league_df), clearing
DP-CATALOG-001/`CATALOGUE_SHRINK_BLOCKED` for sports without any `--allow-catalogue-shrink` override. Not verified live
post-fix in this session (the fix landed at 10:50 local, ahead of the next 01:00 UTC scheduled run) — flagged as a
follow-up verification, not left as an open todo requiring further code work.

- [ ] [OPS] P2. Verify the next scheduled `lifecycle-catalogue-regen-sports` run (next `0 1 * * *` UTC after
      instruments-service@24f84e86 lands on the deployed image) promotes successfully (no `CATALOGUE_SHRINK_BLOCKED`)
      and `prod/catalog.parquet` row count is `>= 27,216`. Repo: instruments-service.

## Not previously tracked

Grepped `plans/active/issues/` for `DP_CATALOG_NOT_RUNNING`, `DP-CATALOG-001/002`, `CATALOGUE_SHRINK_BLOCKED`, and
`lifecycle-catalogue-regen-prediction` — no existing issue doc covers this specific sports-shrink-block / prediction-OOM
pair. `cefi_monotonicity_guard_alerting_and_dark_venues_2026_07_07.md` covers the SAME guard mechanism but for cefi
(dark-venue alerting gap, resolved); this is a new, distinct finding for sports/prediction.

## Open work (tracked todos)

- [x] [OPS] P1. Sports — diagnose the 27,216→27,210 shrink — instruments-service@24f84e86 + evidence: NOT a legitimate
      league-de-registration and NOT upstream flakiness — a real enumerator bug (rolling `SPORTS_FTP_WINDOW_DAYS=400`
      window with no frozen tail). Fixed directly + regression-tested + shipped via quickmerge (see "2026-07-15 — 6-row
      diagnosis + fix" below). Repo: instruments-service.
- [x] [INFRA] P1. Prediction — raise `lifecycle-catalogue-regen-prediction`'s Cloud Run Job memory limit above 4Gi —
      deployment-service@6bfa284: Terraform `lifecycle_catalogue_scheduler.tf` bumped memory 4Gi→16Gi, cpu 2→4 (Cloud
      Run couples the two; 16Gi needs cpu>=4). Sizing informed by live Cloud Monitoring
      `run.googleapis.com/container/memory/utilizations` (highest sampled point 63% of 4Gi ≈2.5Gi in the last full
      minute before each SIGKILL — necessarily an UNDERSTATE of true peak since the container dies ~4s into the
      [BISECT-E] stage, before the next sample) plus the strongest same-AG reference point: prediction's own sibling
      weekly `--mode full` job already runs at 16Gi/cpu4 after OOMing at this SAME 4Gi on 2026-07-04 for a
      comparably-sized "2.5M-row multi-grain aggregate" — the daily incremental job holds the identical 2,673,230-row
      full-catalogue frozen-tail in memory for the guard+promote step, so it needs the same headroom. Live-applied
      immediately via `gcloud run jobs update lifecycle-catalogue-regen-prediction --memory=16Gi --cpu=4` (config
      verified: `cpu: '4', memory: 16Gi`), `terraform fmt`/`tofu validate` clean, deployment-service quality gates green
      (106s), shipped via quickmerge to `live-defi-rollout`. Re-run confirmed the fix: fresh
      `gcloud run jobs execute --wait` → execution `lifecycle-catalogue-regen-prediction-sdzdc` completed successfully
      (exit_code=0, `succeededCount: 1`, no SIGKILL) — for the first time in 3 days it cleared [BISECT-E]:
      `Monotonic guard: new=2673230 current=2673230 decision=ACCEPT (monotonic_ok)` → `CATALOGUE_PROMOTED` event →
      `prod/catalog.parquet` mtime advanced from the frozen 2026-07-14T00:58:37Z to 2026-07-15T10:10:05Z (row count
      unchanged at 2,673,230 since the by_date window itself had 0 new rows that day — the promote-write succeeding, not
      a row-count change, is what fixes the staleness alert). Repo: deployment-service.
- [ ] [INFRA] P3. Grant `lifecycle-catalogue-regen@central-element-323112.iam.gserviceaccount.com`
      `storage.objects.create` on `central-element-323112-events` (or the correct events-sink bucket) so
      `CATALOGUE_SHRINK_BLOCKED`/similar structured events stop silently 403ing out of the event-log sink. Repo:
      deployment-service (IAM) — low priority, Cloud Logging already carries the same signal.
- [ ] [DATA] P1. **cefi `CATALOGUE_SHRINK_BLOCKED` — added per RE-TRIAGE (2026-07-23) recommendation, still unresolved
      as of that check.** `lifecycle-catalogue-regen-cefi` has hit `CATALOGUE_SHRINK_BLOCKED` on 07-16 and again on
      07-23 (`new=428410 < current=429129`); today's drop-list is dominated by `dropped_delisted` expired-derivative
      contract IDs (DERIBIT/OKX-FUTURES/BINANCE-DELIVERY/BINANCE-FUTURES/KRAKEN-FUTURES) — the same "aged out of the
      window, no frozen tail" bug class already fixed for sports (`_merge_sports_ftp_with_frozen_tail`,
      `instruments-service@24f84e86`) but never generalized to cefi. Generalize the frozen-tail merge fix to the cefi
      `_merge_incremental` path and re-run `lifecycle-catalogue-regen-cefi` to confirm `CATALOGUE_PROMOTED`. Repo:
      instruments-service.

## Progress Log

- 2026-07-15: Filed by background investigation agent dispatched to check whether the same-session instruments-service
  tradfi corp-actions commit (`03f71c81a`) caused this staleness. Regression CLEARED (different script/artifact +
  tradfi-scoped edit + timing precludes causation — see above). Root-caused both alerts via live
  `gcloud run jobs executions list` + `gcloud logging read` + `gsutil stat` (no code changes made; diagnosis only).
- 2026-07-15 (follow-up): Dispatched per operator decision to investigate the sports 6-row shrink before deciding on
  `--allow-catalogue-shrink`. Reproduced the roll-up read-only against live prod GCS, identified the exact accounting (9
  rows aged off the FTP grain's rolling 400-day window, 3 new same-day fixtures gained, net −6 — see "2026-07-15 —
  sports 6-row diagnosis + fix" above), reached a BUG verdict (not legitimate, not transient), and fixed it directly per
  the operator's pre-authorized "bug → fix + test + ship" branch: instruments-service@24f84e86 (frozen-tail merge for
  the sports FTP grain via the existing `_merge_incremental` engine), 2 new regression tests, quality gates green,
  shipped via quickmerge to `live-defi-rollout`. Did NOT run `--allow-catalogue-shrink` (out of scope per operator
  instruction — that remains a human/operator-facing override action, moot now that the underlying bug is fixed). Left
  one P2 follow-up todo to verify the next scheduled run actually promotes clean.
- 2026-07-15 (prediction OOM fix): Dispatched per the pre-existing precedent this session (manifest-consolidator memory
  bumps via Terraform + live-apply) to fix the prediction half of this issue. Found the Terraform resource
  (`deployment-service/terraform/gcp/lifecycle_catalogue_scheduler.tf`, `lifecycle_catalogue_asset_groups` local),
  pulled live Cloud Monitoring memory-utilization samples (inconclusive on true peak — container dies too fast after the
  last sample) and cross-checked prediction's own weekly full-rebuild job (already 16Gi/cpu4 after an OOM on a
  comparably-sized aggregate), bumped the daily job to match (4Gi/cpu2 → 16Gi/cpu4), live-applied via
  `gcloud run jobs update`, and shipped the Terraform change: deployment-service@6bfa284 (quickmerge, quality gates
  green 106s; hit one branch-drift retry mid-ship — `git pull --rebase --autostash`, re-verified content-scoped
  sentinel, re-ran quickmerge clean). Confirmed the fix with a fresh `gcloud run jobs execute --wait`: the job cleared
  the monotonic-guard/promote-write stage for the first time in 3 days (exit_code=0, `CATALOGUE_PROMOTED`,
  `prod/catalog.parquet` mtime advanced past the frozen 2026-07-14T00:58:37Z). Flipped the P1 prediction todo to done
  with full evidence. Both root-caused alerts (sports shrink-block, prediction OOM) now have shipped fixes; only the P2
  sports-verification and P3 IAM-403 todos remain open.

## 2026-07-16 update — Group-C fleet triage: cefi + defi ALSO hitting `CATALOGUE_SHRINK_BLOCKED` (different root cause, NOT fixed)

Found while triaging the "Group-C fresh-image job failures" sub-finding from `utl_uac_skew_fleet_audit_2026_07_15.md`.
`lifecycle-catalogue-regen-cefi` and `lifecycle-catalogue-regen-defi` are BOTH failing on today's (2026-07-16 01:0x UTC)
scheduled run, on a fresh post-06-09 image — same DP-CATALOG-001/`CATALOGUE_SHRINK_BLOCKED` alert class as the
sports/prediction incidents above, same code file (`build_instrument_catalogue.py`), but a **DIFFERENT** root cause from
either of those two fixes (not the sports FTP-no-merge bug, not an OOM):

- **cefi**: `Monotonic guard: new=424599 current=427552 decision=REJECT` (`CATALOGUE_SHRINK_BLOCKED`, −2,953 rows).
- **defi**: `Monotonic guard: new=10378 current=10387 decision=REJECT` (`CATALOGUE_SHRINK_BLOCKED`, −9 rows).
- Both confirmed via live `gcloud logging read` on 2 consecutive execution attempts each (identical row counts both
  times — not a flake).

**Root-cause hypothesis (evidenced, not yet fixed): duplicate cefi-perp lineage merge-keys in the PREVIOUS catalogue,
partially collapsed by `_merge_incremental`'s opportunistic dedup.** Downloaded the live `prod/catalog.parquet` for both
AGs and re-ran `_incremental_merge_keys()` (the exact function from `build_instrument_catalogue.py`, mirrored read-only)
over them:

- cefi: 427,552 rows → only 423,733 distinct merge keys — **2,820 duplicate-key groups, 3,819 "excess" rows** that
  should collapse to one lifecycle each. Sample: `cefiperp::HYPERLIQUID::BCH::LINEAR` has 3 rows —
  `HYPERLIQUID:PERP:BCH`, `HYPERLIQUID:PERPETUAL:BCH-USD`, `HYPERLIQUID:PERPETUAL:BCH-USD@LIN` — exactly the "2026-07
  id-convention churn" the function's own docstring describes as the reason the perp lineage key exists ("collapses to
  ONE lifecycle instead of 3 stale-dup listings").
- defi: 10,387 rows → 10,370 distinct keys — 17 duplicate groups / 17 excess rows (same DRIFT-SOLANA `PERP:X` vs
  `PERPETUAL:X` pattern).
- This is the SAME class of issue the code's own comment already names as precedent: _"the 122-dupe cefi
  CATALOGUE_SHRINK_BLOCKED on the first weekly self-heal (2026-07-04)"_ — i.e. this has happened before and was
  presumably absorbed by a `--mode full` weekly rebuild (which recomputes the whole catalogue and naturally collapses
  every duplicate key in one pass) rather than a code fix to the incremental path.
- **Why it's only shrinking PART of the dupes today, not all 3,819 at once**: `_merge_incremental`'s `tail` branch drops
  ALL prev rows whose key appears anywhere in window (`~prev_keys.isin(window_key_set)`), but `updated` is built from
  raw window rows (`window[known_mask]`) with **no dedup by merge key** — so a duplicate-key group only collapses to one
  surviving row when the trailing window happens to touch it (today's window: `day>=2026-06-25`), and any duplicate
  group entirely outside the window stays un-collapsed in `tail`. This explains the accounting exactly: cefi's 23,493
  prev rows-with-key-in-window minus 19,870 `updated` rows = 3,623 collapsed today (most, not all, of the 3,819 total
  latent dupes — the rest will trickle out over future days as the widening window eventually touches them, tripping the
  guard again and again until either (a) a `--mode full` weekly rebuild fully collapses them in one shot, or (b) the
  incremental merge is fixed to proactively dedupe ALL known-duplicate prev keys, not just window-touched ones).

**NOT fixed this session — filed here instead, per the findings-triage rule** (ambiguous / data-correctness judgment
call, not a small-clear ≤30min fix): this could be read either as (a) a legitimate corrective dedup (in which case
`--allow-catalogue-shrink` on today's already-computed 424599/10378-row output is the correct unblock — the code's own
error message literally suggests this override for "a legitimate corrective shrink"), or (b) a latent correctness gap in
`_merge_incremental`'s duplicate-key handling that should be fixed at the root (dedupe `updated` by merge key, keeping
deterministic tie-break) so the guard doesn't keep tripping intermittently as the window walks over the remaining ~3,600
(cefi) / few (defi) not-yet-collapsed dupes. Recommend whoever picks this up: (1) confirm no row in either duplicate
group represents a GENUINE distinct listing (spot-checked the sample rows above — they are the same instrument under 3
successive naming conventions, not 3 different instruments, so (a) looks likely correct), then either run
`--allow-catalogue-shrink` for cefi+defi's next run or ship a proper root-cause fix to `_merge_incremental` mirroring
the `_merge_sports_ftp_with_frozen_tail` precedent (dedupe fully, not opportunistically). **Also affects the weekly
`lifecycle-catalogue-full-defi` and `lifecycle-catalogue-full-tradfi` jobs**, whose last (2026-07-11) executions also
failed — not deep-dived this session (weekly cadence, next run 2026-07-18, lower urgency), but worth checking against
the same hypothesis when this is picked up.

Not fixed by me: this is instruments-service reference-data correctness territory requiring a real judgment call on
whether the shrink is legitimate, which the findings-triage rule reserves for diagnosis + escalation, not a unilateral
fix. Flagging as a **NOTIFY-OPERATOR class finding** (data-pipeline correctness, instruments-service catalogue SSOT) —
operator should decide (a) vs (b) above before anyone runs `--allow-catalogue-shrink` on production reference data.

## RE-TRIAGE (2026-07-23)

**Verdict: RESOLVED BY LATER WORK — for the doc's TITLE claim (sports + prediction DP_CATALOG_NOT_RUNNING).** The
cefi/defi addendum below the title claim is a mixed picture, re-verified live and reported here for completeness.

**Core title claim (sports + prediction) — CONFIRMED FIXED, live-verified 2026-07-23:**

- `gs://instruments-store-sports-prd-.../prod/catalog.parquet` — `Update time: 2026-07-23 01:06:30 GMT` (~7.7h old at
  check time, well under the 24h DP-CATALOG-001 threshold).
- `gs://instruments-store-pred-prd-.../prod/catalog.parquet` — `Update time: 2026-07-23 01:03:17 GMT` (~7.8h old).
- Both jobs (`lifecycle-catalogue-regen-{sports,prediction}`) have been promoting daily without incident since the
  2026-07-15 fixes shipped — no further staleness alerts implied by these fresh timestamps. **`status` kept `open`**
  (not flipped to `resolved`) because the doc's own asset_group also covers cefi/defi and the cefi addendum below is
  confirmed still failing in production — see "cefi/defi addendum" immediately below.

**cefi/defi addendum (2026-07-16 section) — re-verified live 2026-07-23, PARTIALLY still open:**

- **defi: RESOLVED (self-healed, as the doc itself predicted).** Today's execution (`lifecycle-catalogue-regen-defi`,
  `catalogue-rollup-defi-20260723T010110Z`) logged
  `Monotonic guard: new=12187 current=12171 decision=ACCEPT (monotonic_ok)` → `CATALOGUE_PROMOTED`. The widening
  incremental window has now collapsed the residual duplicate keys, exactly per the doc's own "(a) a `--mode full`
  weekly rebuild ... or (b) trickle out over future days" framing — option (b) happened on its own, no code fix needed.
- **cefi: STILL OPEN, confirmed failing TODAY.** `lifecycle-catalogue-regen-cefi`'s 2026-07-23 01:00 UTC run logged
  `Monotonic guard: new=428410 current=429129 decision=REJECT (shrink_blocked)` →
  `CATALOGUE_SHRINK_BLOCKED: new=428410 < current=429129` (exit_code=1) — same failure class as 07-16, still unresolved
  7 days later. **New nuance found in today's log** (not chased further, flagging for whoever picks this up): today's
  drop-list is dominated by `dropped_delisted: 576` / `dropped_active: 0` across DERIBIT (486), OKX-FUTURES (76),
  BINANCE-DELIVERY (8), BINANCE-FUTURES (4), KRAKEN-FUTURES (2) — expired-derivative contract IDs (e.g.
  `...@INV-20260627`, 26 days past expiry) — which looks more like the sports-FTP-style "aged out of the window, no
  frozen tail" bug than the "duplicate perp-lineage merge-key" hypothesis this doc originally proposed for cefi. Both
  mechanisms point at the same `_merge_incremental` gap already fixed for sports (`_merge_sports_ftp_with_frozen_tail`,
  `instruments-service@24f84e86`) but never generalized to cefi. This is a confirmation that cefi remains genuinely
  broken, not a new separate doc-worthy finding (`group_c_cloud_run_job_failures_triage_2026_07_16.md` already
  cross-references this exact addendum as living in this doc, so no fork needed) — recommend the pending [ ] P3 IAM todo
  be joined by a new cefi-specific todo generalizing the frozen-tail fix, next time this doc (or a successor) is worked.
