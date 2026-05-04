---
title: "instruments-service to 100% honest coverage across all 5 asset groups (EOD 2026-05-04)"
priority: P0
status: active
owner: harsh
created: 2026-05-04
type: deployment
epic: data-pipeline-completion
completion_gates:
  code: none
  deployment: D2
  business: none
repo_gates:
  - repo: instruments-service
    deployment: D2
depends_on:
  - instruments_and_market_tick_data_completion_2026_05_01
isProject: false
---

## Status snapshot (2026-05-04 13:15 IST — end of session)

**Phase 0 (diagnose) — DONE.** Per-asset-group dry-runs completed; phantom counts known.
**Phase 1 (flip phantoms) — DONE for cefi/tradfi/sports.**
- cefi: 12,540 phantoms flipped to `attempted_failed`
- tradfi: 2,726 phantoms flipped
- sports: 41,223 phantoms flipped (SFI excluded)
- prediction: 11,848 phantoms found but **out of scope** (POLYMARKET/`trades` is MTDS data)
- defi: 597 phantoms found, deferred (low priority)

**Phase 2 (backfill) — NOT DONE, two blockers:**

1. **Local cefi/tradfi backfill via `run_vm_backfill_e2e.sh` failed silently** — runner
   doesn't export `GCP_PROJECT_ID`, so every chunk aborts at bootstrap. Re-fire commands
   with corrected env are in the "Pending work" section below. ~Easy fix.
2. **Sports VM launches blocked on IAM** — `harshkantariya@odum-research.com` lacks
   `roles/iam.serviceAccountUser` on the Compute SA. Ikenna needs to grant. Fallback:
   run sports adapters locally too (same Python CLI; needs `GCP_PROJECT_ID` env). Singleton
   lock would be bypassed — risk of API thrash if other agents launch sports VMs in parallel.

**Net**: nothing's been actually backfilled today. Manifests are honest now (phantoms
flipped → orchestrator will retry on next launch), but the launches haven't happened.
Resume tomorrow once the env-var fix is applied + IAM grant lands.

## Context

Scope of *this* plan is narrower than the parent epic
(`instruments_and_market_tick_data_completion_2026_05_01.plan.md`):

- **Service**: `instruments-service` only — instrument-definition shards, not market-tick or
  market-data-processing.
- **Asset groups**: all five — `cefi`, `tradfi`, `sports`, `prediction`, `defi`.
- **Target**: ≥99% `captured + empty_confirmed` under the secondary-cutoff denominator (per
  parent-epic success criteria) by EOD 2026-05-04.
- **Non-goals (this plan)**: deployment-ui Phase 0 bug fixes (deferred — Harsh will pick up
  later), market-tick-data backfills, MDPS candle generation, sports % drive (in flight by
  another agent).

**Why a separate plan**: parent epic has Phase 0 (UI) → Phase 1 (sports tick) → Phase 2 (cefi)
→ etc. as a sequential DAG. Today's "instruments-only to 100%" cuts a horizontal slice across
all asset groups for a single service. Tracking it separately keeps the parent epic clean and
gives a tight EOD success criterion.

**Background discoveries from this session (2026-05-04)** that shape this plan:

- `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` is the right diagnostic
  — supports all 5 asset groups via `ASSET_GROUP_CONFIG`, probes both `category=` (legacy) and
  `asset_group=` (canonical) hive keys to avoid the 2026-05-01 false-181k-phantoms incident on
  cefi.
- `reconcile_phantom_manifest_rows.py` (no `_all` suffix) is sports-only. Don't use it for
  cefi/tradfi/defi/prediction.
- The `deployment-ui` Deploy button does **not** spawn VMs locally (no orchestrator worker
  runs in T2 dev). VM-spawning is done via the shell launchers in
  `deployment-service/scripts/vm/launch-*.sh` directly. Harsh's teammate's 31 running VMs all
  came from those launchers.
- The cloud `deployment-dashboard` Cloud Run service exists but is in failed state since
  2026-04-30 (`Ready=False`, container failed startup). T3 is non-functional. T2 is the SSOT.
- Per CLAUDE.md and the playbook, the canonical workflow is:
  ```
  1. reconcile dry-run (per asset group)        — diagnose
  2. reconcile (no --dry-run) for any phantoms  — flip stale captured→attempted_failed
  3. launch backfill VMs                        — orchestrator now retries the failed shards
  4. wait, re-run reconcile dry-run             — verify zero phantoms remain
  5. verify drilldown / GCS spot-check          — confirm ≥99%
  ```

## Cutoffs (per playbook + UAC `coverage_starts.py`)

Same cutoffs as parent epic — repeated here so this plan is self-contained:

| Asset group | Start (global)             | End   | Per-shard secondary clip                     |
| ----------- | -------------------------- | ----- | -------------------------------------------- |
| CEFI        | 2019-01-01                 | today | per-venue inception (`CEFI_SOURCE_COVERAGE_START`) |
| TRADFI      | 2019-01-01                 | today | per-ticker listing (`TRADFI_TICKER_COVERAGE_START`) |
| SPORTS      | 2020-06-01                 | today | per-source + prediction-vs-reference league filter |
| PREDICTION  | 2020-06-12 (POLYMARKET)    | today | per-venue + per-sub-category (`PREDICTION_SOURCE_COVERAGE_START`) |
| DEFI        | per-protocol launch        | today | per-protocol-per-chain (`DEFI_SOURCE_COVERAGE_START`) |

Always pass the **global** start. Launchers + manifest writers handle the secondary clip
through UAC `clip_dates_to_source_coverage` / equivalents — pre-launch days land as
`empty_confirmed`, not `attempted_failed`.

## Execution DAG

```
Phase 0 (Diagnose, parallel)
   ├── reconcile dry-run cefi
   ├── reconcile dry-run tradfi
   ├── reconcile dry-run sports
   ├── reconcile dry-run prediction
   └── reconcile dry-run defi
        │
        ▼  (review numbers; decide what to launch)
Phase 0.5 (Sports gate — verify in-flight work has settled before launching new sports VMs)
        │
        ▼
Phase 1 (Flip phantoms, parallel — only for asset groups with non-zero phantoms)
        │
        ▼
Phase 2 (Launch backfills, parallel by asset group)
        │
        ▼  (wait — VMs run hours/days)
Phase 3 (Verify, parallel)
        │
        ▼
Phase 4 (Sign-off + plan close)
```

Realistic ETA caveat: Phase 2 wall time depends on shard count. CEFI 2019-→today across 9
venues has ~22k potential shards. Even with 100 concurrent VMs and ~5 min per shard, that's
~18 hours. **EOD target may slip into the next day** if the gap is large; we'll know after
Phase 0 dry-runs.

## Phase 0 — Diagnose (read-only, parallel)

**Scope nit before starting**: "instruments at 100%" can mean two things:

1. **Per-day shard coverage**: every `(asset_group, venue, day)` tuple in the cutoff window has
   a manifest row in `captured + empty_confirmed`. The reconciler measures this.
2. **Per-instrument completeness on captured days**: each captured day's parquet contains
   every instrument that was tradeable on that day on that venue.

The reconciler dry-run only measures (1). (2) requires a separate per-row content audit.

- [ ] [HUMAN] P0. Confirm with Ikenna which "100%" he means before launching backfills. If
      (2), the work is much larger (we'd need a content-validation script per AG, none
      exists generically today). Default assumption for now: **(1)**.

For each asset group, dry-run the reconciler to learn:

- Total manifest rows scanned
- Phantom rows found (claimed `captured` but no parquet)
- Real `captured` count
- Real `attempted_failed` count
- Missing-row count under the secondary cutoff

Run each in its own terminal/background — they're independent. Per script docstring, bulk-list
pattern is ~5 min for 600k rows per asset group.

- [ ] [SCRIPT] P0. Dry-run cefi:
      ```bash
      cd ~/unified-trading-system-repos/instruments-service
      .venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py \
        --asset-group cefi --dry-run 2>&1 | tee /tmp/recon-cefi.log
      ```
- [ ] [SCRIPT] P0. Dry-run tradfi: same as above with `--asset-group tradfi`, log to
      `/tmp/recon-tradfi.log`.
- [ ] [SCRIPT] P0. Dry-run sports: same with `--asset-group sports`, log to
      `/tmp/recon-sports.log`. **Note**: sports manifest is the in-flight one; numbers may
      shift as the consolidator daemon merges. Re-run if anomalies appear.
- [ ] [SCRIPT] P0. Dry-run prediction: same with `--asset-group prediction`, log to
      `/tmp/recon-prediction.log`.
- [ ] [SCRIPT] P0. Dry-run defi: same with `--asset-group defi`, log to `/tmp/recon-defi.log`.
- [ ] [HUMAN] P0. Review all five logs. Capture the per-asset-group counts in this plan's
      Notes section so we have a baseline. Decide: which asset groups need phantom flips
      (Phase 1)? Which need backfill VMs (Phase 2)?

## Phase 0.5 — Sports gate (partial — SFI excluded from this run)

Per parent-epic Phase 0.5 — sports backfill VMs share league partitions, so collisions cause
double-writes and manifest noise. As of session start (2026-05-04 11:30 IST):

- **SFI (`soccer_football_info`) has 1 instruments-service VM running** for sports
  backfill. **This plan EXCLUDES SFI** — do not launch any new SFI backfill or run sports
  reconciler with SFI data types in scope. Other sports sources (api-football, transfermarkt,
  footystats, understat, openmeteo) are eligible if their gate query is clean.

- [ ] [HUMAN] P0. Confirm the SFI VM is the only in-flight sports work, and capture which
      data types it's covering (so we know what NOT to touch):
      ```bash
      gcloud compute instances list \
        --filter='name~"^(af|tm|sfi|fs|manifest-consolidator)-"' \
        --format='table(name,status,zone,creationTimestamp)'
      ```
      Expected: only the SFI VM + optional `manifest-consolidator-*`. If `af` / `tm` / `fs`
      VMs are also RUNNING — stop and ping the other agent's owner.
- [ ] [SCRIPT] P0. When running sports phantom recon, scope away from SFI to avoid racing
      its writes:
      ```bash
      .venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py \
        --asset-group sports --dry-run \
        --data-types FIXTURES,FIXTURE_EVENTS,STANDINGS,LEAGUES,TEAMS,PLAYER_STATS,ODDS,PLAYER_VALUES,TRANSFERMARKT_LEAGUES
      ```
      (Replace data-types list with the non-SFI set Phase 0 reveals as relevant.) **Do NOT**
      include `SFI_LEAGUES` or `SFI_PROGRESSIVE_STATS` while SFI VM is running — its
      writes are mid-flight and reconciler reads would race them.
- [ ] [HUMAN] P0. Snapshot sports drilldown headline coverage. Per parent-epic Phase 0.5,
      should be ≥80% captured.

## Phase 1 — Flip phantoms (parallel, only for AGs with phantoms > 0)

Run *without* `--dry-run` only for asset groups where Phase 0 found phantoms. This is fast
(same bulk-list pattern as dry-run, plus a single manifest write per asset group).

**Critical**: do NOT write empty placeholder parquets to mask phantoms. Per CLAUDE.md
manifest-phantom-audit rule: `record_empty(...)` is for legitimately-empty source responses
only. Phantoms must be flipped to `attempted_failed` so VMs re-attempt them.

- [ ] [SCRIPT] P0. Flip phantoms for each AG with phantom_count > 0:
      ```bash
      .venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py --asset-group <ag>
      ```
      (no `--dry-run`). Repeat per asset group.
- [ ] [SCRIPT] P0. Re-run dry-run for each flipped AG to confirm phantom count → 0.

## Phase 2 — Launch backfills (parallel by asset group)

This is where the actual instruments-service work happens. Critical distinction discovered
in this session (2026-05-04):

**The cefi/tradfi/defi/prediction launchers in `deployment-service/scripts/vm/launch-*-backfill*.sh`
that look like they're for instruments are NOT.** They have `VM_SERVICE=market_tick_data_service`
and `VM_TASK=cefi-backfill` — they download tick data, not instrument definitions. Inspected
the metadata of all 31 currently-running VMs (`cefi-bitfinex-…`, `cefi-okx-swap-…`,
`cefi-deribit-…`, etc.) — they're all MTDS, not instruments-service.

**Launchers that actually run instruments-service** (verified by
`grep VM_SERVICE=instruments_service` across `deployment-service/scripts/vm/`):

- `launch-instruments-smoke-vm.sh` — single-day smoke test (writes to `*-test-` buckets,
  not prod)
- `launch-{api-football,transfermarkt,sfi,footystats,understat,openmeteo}-backfill-vm.sh`
  — sports instruments only
- `launch-sfi-forward-poll.sh`, `launch-footystats-forward-poll.sh` — daily forward-poll
  (live, not backfill)
- `launch-sports-manifest-rescan-vm.sh` — sports manifest rescan only

For **cefi/tradfi/defi/prediction instruments**, **no dedicated VM launcher exists**. The
canonical local-driver script is
[`instruments-service/scripts/run_vm_backfill_e2e.sh`](../../../instruments-service/scripts/run_vm_backfill_e2e.sh)
(despite the name "vm" it runs locally — it invokes `.venv/bin/instruments-service ...` on
whatever machine you run it on, with checkpointing + parallel chunks). Two paths to use it:

**Path A — local driver (simplest, fine for small gaps)**: run `run_vm_backfill_e2e.sh`
directly on this machine. Resumable via checkpoints, so safe to interrupt. **IP-rate-limited
to your laptop's IP** — fine for instruments-service (low API volume, tiny payloads), bad
for tick-data scale.

**Path B — wrap in a VM (ad-hoc)**: write a one-line `gcloud compute instances create` that
sets `VM_SERVICE=instruments_service`, `VM_OPERATION=download`, `VM_ASSET_GROUP=…`,
`VM_VENUE=…`, `VM_START_DATE`, `VM_END_DATE` — same metadata pattern as
`launch-instruments-smoke-vm.sh` but with prod buckets (no `IS_TEST_RUN=true`). Defer to
Ikenna before doing this — the smoke launcher exists, the prod-equivalent doesn't, and
adding one new pattern is something he'd want to bless.

**Cost model (correction to common intuition)**: VMs in this stack have
`VM_SHUTDOWN_ON_COMPLETION=true` — each one self-deletes when its shard finishes.
Cost ≈ `(shard_count × per-shard_runtime × $0.07/hr)` on `e2-standard-2`. **Many
short-lived VMs are NOT inherently expensive** — what matters is total runtime. For
instruments-service the per-shard runtime is small (low API volume). The 31 currently-running
MTDS VMs cost ~$52/day at full burn; instruments-service backfill at the same scale would
cost a fraction of that since shards finish in minutes. Don't switch to a long-lived
single-VM model — that costs more (idle time billed) and breaks shard-level failure isolation.

**Tarball refresh**: per CLAUDE.md, refresh only if **instruments-service / UAC / UTL** code
changed. Today's session changed only deployment-api + deployment-service routes (irrelevant
to backfill VMs). **No tarball refresh needed.** If unsure:
```bash
bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group <X>
```

**`--force` warning**: every launcher / CLI accepts a force flag (the deploy form defaults
it to `true`, but for these scripts default is `false`). With `force=true`, the orchestrator
re-fetches every shard regardless of `_should_skip_shard` — billable API cost, possible
rate-limit hit. **Use `force=false` for daily gap-fill.** Reserve `force=true` for retesting
one specific shard or after a code-fix that requires re-running known-bad data.

### CEFI

- [ ] [HUMAN] P0. Confirm Phase 0 cefi gap (review `/tmp/recon-cefi.log`).
- [ ] [HUMAN] P0. **Pick path** — local-driver (Path A, fast iteration) or VM-wrap (Path B,
      needs Ikenna sign-off). For the per-asset-group counts likely seen at 85% baseline,
      Path A is probably enough.
- [ ] [HUMAN] P0. Path A launch (per CEFI venue):
      ```bash
      cd ~/unified-trading-system-repos/instruments-service
      bash scripts/run_vm_backfill_e2e.sh \
        --venue BINANCE-SPOT \
        --asset-group CEFI \
        --start-date 2019-01-01 --end-date $(date -u +%Y-%m-%d) \
        --chunk-days 30 --parallel 4
      ```
      Repeat for each CEFI venue with a non-trivial gap (BINANCE-FUTURES, DERIBIT, BYBIT,
      OKX, UPBIT, COINBASE, HYPERLIQUID, ASTER). The script chunks the date range,
      parallel-runs `--parallel` chunk workers, and checkpoints to
      `.backfill-checkpoints/<venue>/<chunk>.done` so re-runs skip completed chunks.
- [ ] [HUMAN] P1. Watch progress via the checkpoint dir:
      `ls instruments-service/.backfill-checkpoints/CEFI/<venue>/ | wc -l`.

### TRADFI

- [ ] [HUMAN] P0. Confirm Phase 0 tradfi gap (review `/tmp/recon-tradfi.log`).
- [ ] [HUMAN] P0. Same Path A pattern as CEFI, per TradFi venue:
      ```bash
      bash scripts/run_vm_backfill_e2e.sh \
        --venue CME --asset-group TRADFI \
        --start-date 2019-01-01 --end-date $(date -u +%Y-%m-%d) \
        --chunk-days 30 --parallel 4
      ```
      Repeat for `CBOE`, `NASDAQ`, `NYSE`, `ICE`, `FX`, `POLYGON`, `FRED` if their slice is
      red. Per-ticker listing-date clip is shipped (`TRADFI_TICKER_COVERAGE_START` UAC
      `15b9e74`), pre-listing days auto-skip.

### SPORTS — instruments-service backfill, with SFI excluded

- [ ] [HUMAN] P0. **GATE**: Phase 0.5 must confirm only the SFI VM is running. Other
      sources (af/tm/fs/understat/openmeteo) clear to launch.
- [ ] [HUMAN] P0. Sports has dedicated launchers (`VM_SERVICE=instruments_service`
      confirmed in metadata). Pick the launcher matching the data-type slice that's red in
      `/tmp/recon-sports.log`. **Do NOT touch SFI** while its VM is running — skip
      `launch-sfi-backfill-vm.sh` and `launch-sfi-forward-poll.sh`.
      ```bash
      # api-football (LEAGUES, TEAMS, FIXTURES, FIXTURE_EVENTS, STANDINGS, INJURIES, …)
      bash ~/unified-trading-system-repos/deployment-service/scripts/vm/launch-api-football-backfill-vm.sh \
        --data-type <X> --start-date 2020-06-01

      # transfermarkt (PLAYER_VALUES, TRANSFERMARKT_LEAGUES)
      bash .../launch-transfermarkt-backfill-vm.sh --data-type <X> --start-date 2020-06-01

      # footystats / understat / openmeteo — same pattern
      ```
      For non-prediction reference leagues, scope to FIXTURES + FIXTURE_EVENTS + STANDINGS
      only — per parent-epic prediction-vs-reference cutoff rule. The orchestrator's
      `_should_skip_shard` + `_should_skip_reference_league` guards handle this; pass
      `--leagues prediction|reference|all` if the launcher accepts it.
- [ ] [SCRIPT] P0. After each non-SFI launcher batch completes, re-run sports phantom recon
      (no `--dry-run`) **with the same `--data-types` scope as Phase 0.5** (i.e. excluding
      SFI_LEAGUES / SFI_PROGRESSIVE_STATS until the SFI VM is done).

### PREDICTION

- [ ] [HUMAN] P0. Confirm Phase 0 prediction gap (review `/tmp/recon-prediction.log`).
- [ ] [HUMAN] P0. **No dedicated launcher exists**. Use Path A (local driver):
      ```bash
      bash scripts/run_vm_backfill_e2e.sh \
        --venue POLYMARKET --asset-group PREDICTION \
        --start-date 2020-06-12 --end-date $(date -u +%Y-%m-%d) \
        --chunk-days 30 --parallel 2
      bash scripts/run_vm_backfill_e2e.sh \
        --venue KALSHI --asset-group PREDICTION \
        --start-date 2021-07-19 --end-date $(date -u +%Y-%m-%d) \
        --chunk-days 30 --parallel 2
      ```
      Lower `--parallel` (2 not 4) since PREDICTION venues have stricter rate limits.
- [ ] [HUMAN] P1. Per-sub-category cutoffs (crypto/macro/football for POLYMARKET) — handled
      by the adapter's internal coverage clip; pass venue-only here.

### DEFI

- [ ] [HUMAN] P0. Confirm Phase 0 defi gap (review `/tmp/recon-defi.log`).
- [ ] [HUMAN] P0. **No dedicated launcher exists**. Use Path A per DeFi venue:
      ```bash
      bash scripts/run_vm_backfill_e2e.sh \
        --venue AAVEV3-ETHEREUM --asset-group DEFI \
        --start-date 2022-03-16 --end-date $(date -u +%Y-%m-%d) \
        --chunk-days 30 --parallel 4
      bash scripts/run_vm_backfill_e2e.sh \
        --venue UNISWAPV3-ETHEREUM --asset-group DEFI \
        --start-date 2021-05-05 --end-date $(date -u +%Y-%m-%d) \
        --chunk-days 30 --parallel 4
      # Repeat per (protocol × chain) — see UAC DEFI_SOURCE_COVERAGE_START for inception dates.
      ```
      DeFi instruments are monotonically-increasing (immutable contracts) per the
      orchestrator high-watermark logic — `_should_skip_shard` + per-venue HWM means most
      days will auto-skip. Only red shards re-run.

## Phase 3 — Verify (parallel)

- [ ] [SCRIPT] P0. For each asset group: re-run `reconcile_phantom_manifest_rows_all.py
      --asset-group <X> --dry-run` and confirm phantom count is 0.
- [ ] [HUMAN] P0. Snapshot the deployment-ui drilldown for `service=instruments-service` per
      asset group. Each should show ≥99% `captured + empty_confirmed` under the secondary-
      cutoff denominator.
- [ ] [HUMAN] P1. Spot-check 5 random `(asset_group, day, venue, instrument_type)` rows:
      follow each to its canonical GCS path and confirm the parquet exists.

## Phase 4 — Sign-off + plan close

- [ ] [HUMAN] P0. Update parent epic
      (`instruments_and_market_tick_data_completion_2026_05_01.plan.md`) progress notes:
      mark instruments-service slice complete, link to this plan.
- [ ] [HUMAN] P0. Brief Ikenna on results vs the EOD target.
- [ ] [AGENT] P2. Mark this plan complete and move to `plans/archive/`.

## Files / commands referenced

| Repo                  | File / command                                                  | Phase |
| --------------------- | --------------------------------------------------------------- | ----- |
| instruments-service   | `scripts/reconcile_phantom_manifest_rows_all.py`                | 0,1,3 |
| instruments-service   | `scripts/run_vm_backfill_e2e.sh` (local-driver, resumable)      | 2     |
| deployment-service    | `scripts/vm/launch-{api-football,transfermarkt,footystats,understat,openmeteo}-backfill-vm.sh` (sports instruments only) | 2 |
| deployment-service    | `scripts/vm/launch-instruments-smoke-vm.sh` (single-day, *-test buckets) | ref |
| unified-api-contracts | `unified_api_contracts/canonical/coverage_starts.py`            | ref   |
| unified-trading-pm    | `codex/14-playbooks/backfill-completion-playbook.md`            | ref   |

**Explicitly NOT used** (these run MTDS / market-tick-data, not instruments-service):
`launch-cefi-sharded-backfill.sh`, `launch-tradfi-backfill-vm.sh`, `launch-mdps-*-backfill*.sh`.

## Success criteria

- All 5 asset groups: ≥99% `captured + empty_confirmed` for `service=instruments-service`,
  scoped to the secondary-cutoff denominator (per parent-epic). **Definition (1) of "100%"**
  per Phase 0 scope-nit; revisit if Ikenna meant (2).
- Phantom recon dry-run reports 0 phantom flips for every asset group (excluding SFI while
  its VM is running).
- Drilldown spot-check: 5 random captured rows per AG resolve to actual parquets in GCS.

## Execution log (2026-05-04 EOD push)

- **12:33–12:48 IST**: Phase 0 dry-runs for cefi/tradfi/sports/prediction/defi (parallel after
  the `tempfile` patch). Sports first attempt timed out on GCS list under 5x parallel load;
  retry with `--workers 16` succeeded.
- **12:46–12:57 IST**: Phase 1 phantom flips for cefi (12,540), tradfi (2,726), sports
  (41,223 SFI-excluded). All wrote manifest back successfully.
- **12:55 IST**: Phase 2 TRADFI backfill fired locally via `run_vm_backfill_e2e.sh` for
  CME/CBOE/NASDAQ/NYSE/ICE/FX (6 venues × 4 chunk-workers = 24 concurrent
  instruments-service procs). No IAM issue — runs on this machine.
- **12:57 IST**: Phase 2 CEFI backfill fired locally for the 9 active CEFI venues
  (9 × 4 = 36 concurrent procs).
- **12:57 IST**: Phase 2 SPORTS af + tm VM launches blocked: `User does not have access to
  service account 1060025368044-compute@developer.gserviceaccount.com. Ask a project owner
  to grant the iam.serviceAccountUser role.`
- **13:10 IST**: Discovered cefi+tradfi local backfills had been silently failing every
  chunk on `GCP_PROJECT_ID must be set in environment` — `run_vm_backfill_e2e.sh` doesn't
  export the env. All 90 chunks per venue × 15 venues showed "START" but never "DONE",
  produced zero checkpoints, wrote nothing to GCS. Killed all in-flight procs, cleaned
  checkpoints + logs.
- **13:08 IST**: Investigation found that the `setup-data-pipeline-vm.sh` script (line 596+)
  for `VM_TASK=sports-backfill` just runs:
  ```
  python -m instruments_service --operation instruments --mode batch \
    --asset-group SPORTS --sports-provider {API_FOOTBALL|TRANSFERMARKT|...} \
    --sports-entity <ENTITY> --start-date <X> --end-date <Y>
  ```
  **The IAM block is NOT a hard blocker — same CLI runs locally** like cefi/tradfi.
  Smoke test confirmed: `.venv/bin/python -m instruments_service ...` accepts the same
  args; only requires `GCP_PROJECT_ID=central-element-323112` env. Can fire all sports
  retries on this laptop without VM access. (Whether this is *desirable* — singleton
  rate-limit lock exists for a reason; running locally bypasses it — see Risks section.)

## Adapter smoke matrix (1 day per venue, 2026-05-01)

Run before any fan-out — confirms the adapter+API+GCS+manifest path is wired per venue.
Command pattern:
```bash
cd ~/unified-trading-system-repos/instruments-service
GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp CLOUD_MOCK_MODE=false \
  .venv/bin/instruments-service \
  --operation instruments --mode batch \
  --asset-group <AG> --venues <VENUE> \
  --start-date 2026-05-01 --end-date 2026-05-01
```

### CEFI smoke results (2026-05-04 13:20 IST)

| Venue            | Status | Records / Fetched      | Notes                                                                                                                                                                                                                                                              |
| ---------------- | :----: | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| BINANCE-SPOT     |   ✅   | 48 / 51                | Tardis `binance` endpoint, healthy.                                                                                                                                                                                                                                |
| BINANCE-FUTURES  |   ✅   | 33 / 37                | Tardis `binance-futures` endpoint, healthy.                                                                                                                                                                                                                        |
| DERIBIT          |   ✅   | 3,720 / 200,312        | Tardis returns full options chain — 200k symbols filtered to 3.7k (BTC/ETH options + perps).                                                                                                                                                                       |
| BYBIT            |   ✅   | 32 / 291               | Tardis `bybit` endpoint, healthy.                                                                                                                                                                                                                                  |
| **OKX**          |   ❌   | —                      | `URDI[OKX]: ADAPTER_ERROR (permanent): No Tardis exchange mapping for canonical venue 'OKX'`. Config bug — UAC `venue_to_tardis` mapping missing for canonical name `OKX`. Sharding config lists `OKX`, but adapter expects `OKX-SPOT` / `OKX-SWAP` / `OKX-FUTURES`. **Not geo-block.** |
| UPBIT            |   ✅   | 12 / 13                |                                                                                                                                                                                                                                                                    |
| **COINBASE**     |   ❌   | 0 records             | `URDI returned zero records for date=2026-05-01 asset_groups=['CEFI']`. Adapter ran but got nothing back. Either bare `COINBASE` is also a sharding-vs-adapter mismatch (canonical might be `COINBASE-SPOT`), or transient API issue. Needs further investigation.   |
| HYPERLIQUID      |   ✅   | 21 / 21                | On-chain CLOB, native API.                                                                                                                                                                                                                                          |
| ASTER            |   ✅   | 19 / 19                |                                                                                                                                                                                                                                                                    |

**7 of 9 CEFI venues healthy. OKX + COINBASE blocked on canonical-venue-name mismatches.**
The Phase 2 backfill should proceed for the 7 working venues; OKX + COINBASE need a fix
in either UAC `venue_to_tardis` map or the sharding YAML before they can run.

### TRADFI / DEFI / SPORTS smoke results

(In progress — will fill in as each matrix completes.)

## Pending work — what to launch when permissions / decisions land

### CEFI / TRADFI — local backfill failed silently, must re-fire with env vars

**Status (2026-05-04 13:10 IST)**: First run of `run_vm_backfill_e2e.sh` for cefi+tradfi
failed on every chunk — the runner doesn't export `GCP_PROJECT_ID` and the
`instruments-service` CLI bootstrap aborts at `log_event("STARTED")` with
`ValueError: GCP_PROJECT_ID or AWS_ACCOUNT_ID must be set in environment`. All chunks
showed "START" but no "DONE", produced no checkpoints, and wrote nothing to GCS.
**Killed and cleaned** — `.backfill-checkpoints/` and `logs/recon-fill-*` removed so
reruns start fresh.

**Re-fire command (must export env first)**:
```bash
cd ~/unified-trading-system-repos/instruments-service
export GCP_PROJECT_ID=central-element-323112
export CLOUD_PROVIDER=gcp
export CLOUD_MOCK_MODE=false

TODAY=$(date -u +%Y-%m-%d)

# CEFI — 9 venues
for venue in BINANCE-SPOT BINANCE-FUTURES DERIBIT BYBIT OKX UPBIT COINBASE HYPERLIQUID ASTER; do
  bash scripts/run_vm_backfill_e2e.sh \
    --venue "$venue" --asset-group CEFI \
    --start-date 2019-01-01 --end-date "$TODAY" \
    --chunk-days 30 --parallel 4 \
    --log-dir "logs/recon-fill-cefi-$venue" > "/tmp/backfill-cefi-$venue.log" 2>&1 &
done

# TRADFI — 6 venues
for venue in CME CBOE NASDAQ NYSE ICE FX; do
  bash scripts/run_vm_backfill_e2e.sh \
    --venue "$venue" --asset-group TRADFI \
    --start-date 2019-01-01 --end-date "$TODAY" \
    --chunk-days 30 --parallel 4 \
    --log-dir "logs/recon-fill-tradfi-$venue" > "/tmp/backfill-tradfi-$venue.log" 2>&1 &
done
wait
```

Resumable via `.backfill-checkpoints/<AG>_<venue>_<range>/`. Cumulative ~60 concurrent
`instruments-service` procs. Smoke-test one chunk first to confirm env propagates:
```bash
GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp \
  .venv/bin/instruments-service --operation instruments --mode batch \
  --asset-group CEFI --venues DERIBIT --start-date 2019-01-01 --end-date 2019-01-03
```
Expected: real progress past the bootstrap log lines (currently it dies at log_event("STARTED")).

**Follow-up bug to file**: `run_vm_backfill_e2e.sh` should export `GCP_PROJECT_ID` /
`CLOUD_PROVIDER` for child invocations, OR at minimum check that they're set before
spawning chunks. Silent fail across 90 chunks per venue with no visible error in the
top-level log was a data quality risk. Tracking under
`instruments-service` (no plan slug yet — Harsh to follow up tomorrow).

### SPORTS — choose one path

**Path 1 (preferred, requires IAM grant) — VM launchers, singleton-locked:**

Ikenna runs as project owner:
```bash
gcloud iam service-accounts add-iam-policy-binding \
  1060025368044-compute@developer.gserviceaccount.com \
  --member="user:harshkantariya@odum-research.com" \
  --role="roles/iam.serviceAccountUser" \
  --project=central-element-323112
```

Then fire:
```bash
bash deployment-service/scripts/vm/launch-api-football-backfill-vm.sh 2020-06-01 2026-05-04
bash deployment-service/scripts/vm/launch-transfermarkt-backfill-vm.sh 2020-06-01 2026-05-04
# (sfi excluded — other agent's VM in flight)
# Optional, if recon shows phantoms in their data types:
bash deployment-service/scripts/vm/launch-footystats-backfill-vm.sh 2020-06-01 2026-05-04
bash deployment-service/scripts/vm/launch-understat-backfill-vm.sh 2020-06-01 2026-05-04
bash deployment-service/scripts/vm/launch-openmeteo-backfill-vm.sh 2020-06-01 2026-05-04
```
Singleton-lock prevents thundering herd against shared API keys. **This is the canonical
path** per the playbook — same pattern your teammate's existing 31 VMs use.

**Path 2 (fallback, no IAM grant needed) — local CLI, manually paced:**

If the IAM grant doesn't land in time, run sports adapters locally one-at-a-time:
```bash
cd ~/unified-trading-system-repos/instruments-service
export GCP_PROJECT_ID=central-element-323112
export CLOUD_PROVIDER=gcp

# api-football — sequential per entity to mimic the singleton lock behavior
for entity in FIXTURES STANDINGS INJURIES PLAYER_STATS FIXTURE_LINEUPS FIXTURE_STATS FIXTURE_EVENTS TEAMS LEAGUES; do
  .venv/bin/python -m instruments_service \
    --operation instruments --mode batch \
    --asset-group SPORTS --sports-provider API_FOOTBALL --sports-entity $entity \
    --start-date 2020-06-01 --end-date 2026-05-04 \
    > /tmp/sports-af-$entity.log 2>&1
done

# transfermarkt — PLAYER_VALUES is the big one (8,647 phantoms)
for entity in PLAYER_VALUES TRANSFERMARKT_LEAGUES TEAM_SQUAD; do
  .venv/bin/python -m instruments_service \
    --operation instruments --mode batch \
    --asset-group SPORTS --sports-provider TRANSFERMARKT --sports-entity $entity \
    --start-date 2020-06-01 --end-date 2026-05-04 \
    > /tmp/sports-tm-$entity.log 2>&1
done
```

⚠️ **Caveat**: this bypasses the singleton lock. If another sports VM (or your
teammate's SFI VM) is hitting the same shared API key, you'll thrash. Before firing
Path 2 confirm `gcloud compute instances list --filter='name~"^(af|tm|fs|understat|openmeteo)-"'`
is empty.

### PREDICTION — out of scope

Phase 0 dry-run found 11,848 phantoms but they're all on POLYMARKET / `trades` data type.
That's MTDS data (market-tick), not `instruments-service` reference data. Either the
prediction manifest is conflating MTDS writes with instruments writes, or the writers are
mis-attributing the asset group. **Flag for Ikenna separately**, do not flip in this plan.

### DEFI — optional cleanup

597 phantoms, all on EIGENLAYER / `rewards`. Not core instruments data. Two choices:
- Skip (0.2% of defi manifest, won't move the headline percentage).
- Flip with `reconcile_phantom_manifest_rows_all.py --asset-group defi` (~5 min,
  no backfill needed, just clears the phantoms so the headline is honest).

## Verification after backfills complete

For each AG:
```bash
cd ~/unified-trading-system-repos/instruments-service
.venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py --asset-group <ag> --dry-run
```
Expected: "No phantoms found. Manifest is clean." If non-zero, the orchestrator's
`_should_skip_shard` skipped some shards as `attempted_failed` → `attempted_failed`
(real failure, not phantom). Check the new `error_reason` distribution to decide
whether to retry, fix the adapter, or accept as legitimate API failure.

## Risks / blockers

- **SFI VM in flight**: while the single SFI instruments VM is running, do NOT touch
  `SFI_LEAGUES` / `SFI_PROGRESSIVE_STATS` data types in either reconciler or launcher
  invocations. Reading the manifest mid-write is OK (atomic GCS object), but flipping
  rows the VM is about to write would race.
- **Cefi/tradfi/defi/prediction instruments have no dedicated VM launcher.** Default path
  is `run_vm_backfill_e2e.sh` running locally on this machine — IP-rate-limited by the
  laptop's egress. For instruments-service this is fine (low API volume); if a particular
  venue's daily fetch is slow, Path B (wrap in a VM) is the upgrade. Defer to Ikenna before
  introducing a new VM-launcher pattern.
- **Wall-clock**: realistic only after Phase 0 dry-run reveals gap size. Instruments-service
  shards are tiny (one daily JSON pull per venue), so even thousands of red shards can
  finish in hours via `run_vm_backfill_e2e.sh --parallel 4`. Tick-data scale doesn't apply.
- **API rate limits**: singleton-locked launchers (`launch-sfi-forward-poll.sh` etc.) refuse
  duplicates by design. Don't bypass with `--force` without explicit reason. Use
  `--parallel 2` instead of `--parallel 4` for prediction venues (POLYMARKET / KALSHI
  rate-limit harder than crypto exchanges).
- **Scope ambiguity**: the (1) vs (2) "100%" question above. Resolve before EOD push.

## Out of scope (for *this* plan — covered by parent epic)

- deployment-ui Phase 0 bug fixes (CSV download, day-shard scroll, schema modal, market-tick
  + market-data-processing unified view).
- market-tick-data-service backfills (parent-epic Phase 2/3/4/5).
- market-data-processing-service candle generation (parent-epic Phase 2).
- VIX futures full-tick chain (parent-epic Phase 3, P2 deferred).
- mbp_10 deep-book for tradfi (parent-epic Phase 3, P2 deferred).

## Notes — Phase 0 dry-run results (2026-05-04 12:33–12:45 IST)

| Asset group | Manifest rows | Captured-in-scope | Real captured | Phantoms | % phantom | Top concentration |
| ----------- | ------------: | ----------------: | ------------: | -------: | --------: | ----------------- |
| cefi        | 1,343,892     | 188,684           | 176,144       | **12,540** | 6.6%   | DERIBIT 3,070; BYBIT 1,834; BINANCE-FUTURES 1,763; OKX-SWAP 1,740; UPBIT 1,352. By data_type: empty=9,757 (schema-4 legacy rows), `trades` 2,501 |
| tradfi      | 32,345        | 26,594            | 23,866        | **2,728**  | 10%    | CBOE 657; ICE 379; CME 373; NASDAQ/NYSE 368 each; FX 330. By data_type: empty=2,472 (schema-4), `ohlcv_*`+`trades`+`tbbo` <70 each |
| sports      | 2,401,547     | 758,465           | 717,242       | **41,223** | 5.4%   | STANDINGS 13,022; INJURIES 9,872; PLAYER_VALUES 8,647; PLAYER_STATS 3,057; FIXTURE_{LINEUPS,STATS} ~2.7k each. SFI excluded (other agent's VM). All venue=`""` (sports keys on league_id, not venue). |
| prediction  | 14,369        | 14,328            | 2,480         | **11,848** | 83%    | POLYMARKET / `trades` 11,831 of 11,848. Almost all phantom — but `trades` is MTDS data, not strict instruments-service |
| defi        | 307,341       | 307,341           | 306,744       | **597**    | 0.2%   | EIGENLAYER / `rewards` (all 597). Effectively clean for instruments. |

### Read of the data

- **cefi**: 12,540 phantoms is real work but tractable — they're spread across the 9 active venues and the 9,757 empty-data_type rows are likely schema-4 legacy that need the same flip-to-`attempted_failed` treatment. Once flipped, the orchestrator will retry. Reasonable target for EOD.
- **tradfi**: 2,728 phantoms, similar shape to cefi. The 2,472 empty-data_type rows are again schema-4 legacy. Should be quick.
- **prediction**: 83% phantom rate is alarming but **the data_type is `trades`** — that's market-tick (MTDS) territory, not `instruments-service` reference data. Almost certainly the prediction manifest is conflating MTDS writes with instruments writes. **Out of scope for this plan**, flag for Ikenna separately.
- **defi**: essentially clean. The 597 EIGENLAYER `rewards` phantoms aren't core instruments either. Could leave as-is or flip in 2 seconds.
- **sports**: still running, will refresh when it completes.

### Decisions

| AG | Phase 1 (flip)? | Phase 2 (launch)? | Notes |
| --- | --- | --- | --- |
| cefi | YES — 12,540 phantoms | YES — after flip | Use `run_vm_backfill_e2e.sh` per venue |
| tradfi | YES — 2,728 phantoms | YES — after flip | Same pattern |
| sports | YES — 41,223 phantoms (SFI excluded) | YES — after flip | Use `launch-{api-football,transfermarkt}-backfill-vm.sh` for affected data types. SFI launchers stay off. |
| prediction | NO | NO | Out of plan scope; `trades` rows are MTDS not instruments. Flag for Ikenna. |
| defi | OPTIONAL — 597 phantoms | NO | EIGENLAYER `rewards` only, not strict instruments. Skip or flip-and-leave. |
