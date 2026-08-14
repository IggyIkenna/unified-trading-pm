---
doc_type: issue
title: lst_rate_honest_coverage — VM monitoring history (2026-07-22..07-26, LST-rates + dex-swaps backfill fleets)
summary:
  Line-cap remediation extraction from plans/active/lst_rate_honest_coverage_2026_07_21.md's Progress Log — the
  contiguous chronological block of VM re-check / preemption-and-resume / T+N-min-health-check entries for the
  `mtds-lst-rates-*` and `mtds-dex-swaps-backfill*` backfill VMs (2026-07-22 19:51 UTC through 2026-07-26 07:56 UTC),
  moved verbatim so the live plan stays comfortably under the 1000-line hard cap. All of it describes now-complete or
  well-superseded backfill runs (LST-rates finished 2026-07-23 02:04 UTC; the dex-swaps fleet's terminal state is
  tracked live in the source plan's own Deferred-work table) — read this only if a deeper citation on a specific
  timestamped check-in is needed.
status: archived
nature: notes
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [defi, history, line-cap-remediation, progress-log, vm-monitoring]
related:
  [
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /plans/active/issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md,
  ]
created: 2026-08-14
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
last_updated: 2026-08-14
supersedes:
superseded_by:
locked_by:
locked_since:
depends_on: []
source:
  [
    plans/active/lst_rate_honest_coverage_2026_07_21.md,
    plans/active/issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md Todo 1,
    line-cap remediation 2026-08-14,
  ]
assigned_role: project_management
drift_direction: none
---

# lst_rate_honest_coverage — VM monitoring history

> Extracted verbatim 2026-08-14 (line-cap remediation, per
> `/plans/active/issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md` Todo 1) from
> `/plans/active/lst_rate_honest_coverage_2026_07_21.md`'s Progress Log. Covers the contiguous chronological block of VM
> re-check / preemption-resume / health-check entries for the `mtds-lst-rates-20260722-181845` and
> `mtds-dex-swaps-backfill*` backfill VMs, 2026-07-22 19:51 UTC through 2026-07-26 07:56 UTC. No other doc was found
> citing a specific timestamped entry inside this range by path (only by SHA/description, which remains valid after this
> move) — see the source plan's own Deferred-work table for the current terminal state instead of re-deriving it from
> this history.

## Extracted Progress Log entries

- **2026-07-22 19:51 → 2026-07-23 01:04 UTC (VM fleet re-checks — both healthy throughout, no intervention needed)** —
  `mtds-lst-rates-20260722-181845` climbed continuously: 2023-03-31 (manifest 3,799 entries) → 2024-09-26 (13,829) →
  2025-01-02 → 2025-04-15 → 2025-07-20 (20,629) → 2025-10-29 (22,951) → 2026-02-02 (25,169), with ~96-103 days processed
  per ~30min window, est. under 1h to completion at final check. `mtds-dex-swaps-backfill` RSS stable ~800-1600MiB
  throughout (nowhere near OOM), manifest climbing 9,323 → 62,147 entries, real rows landing across working shards. Both
  correctly left running.

- **2026-07-23 01:26 UTC (mtds-dex-swaps-backfill VM vanished — likely preempted, resumed)** — at the 01:25 check, the
  VM was no longer in `gcloud compute instances list` output at all (confirmed via `get-serial-port-output` → "resource
  ... not found", i.e. fully deleted, not just stopped). Its `run.log` showed no clean `DEPLOYMENT_COMPLETED`/exit_code
  marker — last entries were healthy `RESOURCE_SAMPLE`s at 01:20:57, consistent with a SPOT preemption (no
  graceful-shutdown message written) rather than a natural completion. Manifest was at 63,850+ entries
  (`process_final=True` climbing steadily), well short of what a full `2023-01-01→2026-07-22` × ~20-shard run would
  produce. **Resume approach differs from the LST-rates VM**: this collector processes per-SHARD full-date-range (not
  day-sequential), and `dex_swaps_handler.py` has genuine per-day `ManifestFreshnessCache`/`is_now_skip_worthy` logic
  (confirmed by reading the code, not assumed) — so the correct, safe resume is a PLAIN relaunch with the SAME
  `--start 2023-01-01 --end 2026-07-22` (no `--force` needed, no date-math), relying on the collector's own
  skip-if-already-captured behavior to avoid re-fetching the ~64k rows already written. Verified all 4 tarballs fresh
  before launching (per the earlier session's tarball- staleness lesson). Relaunched: `mtds-dex-swaps-backfill` (same
  name), SPOT, confirmed RUNNING at launch. T+few-min verification pending — will confirm the freshness-skip is
  genuinely firing (log line "Pre-flight: ... fully covered" or the freshness-cache skip path) rather than blindly
  re-fetching everything.

- **2026-07-23 01:43 UTC (both healthy — dex-swaps resume CONFIRMED working, LST-rates very close)** —
  `mtds-dex-swaps-backfill` (relaunched): manifest at 69,205 entries, up from the pre-preemption 63,850 — confirms the
  freshness-skip logic is genuinely working (picked up past where it left off, not re-fetching from scratch), RSS
  healthy ~1123-1309MiB. `mtds-lst-rates-20260722-181845`: now at `2026-06-07`, ~45 days from the `2026-07-22` target —
  expect completion within ~15-20 min at current pace.

- **2026-07-23 02:04 UTC (Phase 5 #4 `lst_rates` backfill — COMPLETED)** — `mtds-lst-rates-20260722-181845` reached
  `day=2026-07-22` cleanly: `Batch complete: 1801 results collected`, `command exited rc=0`,
  `DEPLOYMENT_COMPLETED ... exit_code=0`, clean self-delete (`VM_SHUTDOWN_ON_COMPLETION=true`). This single VM ran
  continuously and uninterrupted from launch (`2021-08-17`) through completion (`2026-07-22`) — no preemption, no resume
  needed, manifest closed at 29,273 entries for this VM's segment. This is the full end-to-end completion of everything
  Phase 5 #4's genesis-date-validation + Tier-4 DefiLlama fallback + aiodns-resolver fix work enabled earlier this
  session: real EVM LST rates (stETH/wstETH/rETH/cbETH/ankrETH/wBETH/rsETH/ezETH/etc.) and real Solana LST rates
  (mSOL/sanctumSOL/jitoSOL/bSOL) now cover the full `2021-08-17→2026-07-22` window, each correctly gated from its own
  validated genesis date. **Next actionable step** (genuinely unblocked now): run the `lst_yields` FEATURE computation
  over this now-complete `lst_rates` source history — a separate features-service compute step (see the
  `#4 lst_yields backfill` todo — the raw-data gap that blocked it is now closed; the ezETH/rsETH extended EVM rows and
  the Solana rows are both present for their full valid date ranges).

- **2026-07-23 02:05 UTC (lst_yields feature run — checked, correctly deferred to operator)** — with the `lst_rates`
  raw-data backfill now complete, checked whether the `#4 lst_yields backfill` todo (running the `lst_yields` FEATURE
  over this history) is genuinely unblocked and safe to execute myself. Found the only existing runner for this exact
  feature group, `features-service/scripts/backfill_lst_yields_30day.sh`, carries explicit markers: `# owner: operator`,
  `# Operator invocation — do NOT execute from CI`, `# last_executed: NEVER — operator first-run`. This is a real,
  deliberate boundary (not incidental) — the underlying
  `python -m features_service --operation compute --feature-group lst_yields` writes real feature data that feeds
  `carry_staked_basis` (Phase 6 A2, itself already operator-gated on E1/E2/E4 rulings), so running a full-history
  compute myself would cross a line the precedent script explicitly draws. **Correctly left for the operator** — same
  treatment as Phase 5 #1 and Phase 6. The raw-data prerequisite (this session's #4 work) is done; the feature-compute
  step is a distinct, operator-owned action.

- **2026-07-23 02:38 UTC (dex-swaps preempted a SECOND time — resumed again)** — the resumed VM from the earlier 01:26
  relaunch died again at ~01:43 (found on this check, ~54min after the fact — no other alert channel exists for this),
  same signature as before: no clean exit marker, `get-serial-port-output` → instance not found. Checked memory levels
  in the RESOURCE_SAMPLE trail right up to the last log line: 982MiB/12.2% — nowhere near the 85% mem_crit threshold,
  ruling out an OOM cause (unlike the unrelated CEFI Tardis P0 issue). This is consistent with a genuine SPOT reclaim,
  not a code bug — two preemptions in ~2h on a SPOT e2-standard-4 in this zone is plausible bad luck, not a pattern
  requiring escalation (per CLAUDE.md, switching to on-demand for a backfill is itself an anti-pattern; SPOT +
  idempotent resume is the correct, intended design). Relaunched again: same command
  (`--start 2023-01-01 --end 2026-07-22`), all 4 tarballs confirmed fresh, RUNNING. Manifest was at 69,425 entries
  before this second death; the freshness-skip logic should again pick up from there.

- **2026-07-23 02:59 UTC (dex-swaps re-check — healthy after second resume)** — `mtds-dex-swaps-backfill` RUNNING, RSS
  stable ~1036-1062MiB, heartbeats fresh. This VM instance's own per-VM manifest-shard counter reset to a fresh count
  (1,688) as expected — that's this instance's own contribution tally, not a cumulative total across restarts; the
  underlying already-captured swap parquet files + the real coverage manifest persist independent of VM restarts, so
  this is not data loss. No further action needed.

- **2026-07-23 03:30 UTC (dex-swaps re-check — still healthy)** — `mtds-dex-swaps-backfill` RUNNING since the second
  resume, RSS stable ~832-1285MiB, heartbeats fresh, completed another full shard-list pass (75,274 records this pass).
  No further preemptions since 02:38 UTC. Continuing to monitor.

- **2026-07-23 04:01 UTC (dex-swaps re-check — still healthy, stable ~1.5h since last preemption)** — manifest at 15,406
  entries (this instance), RSS stable ~886-1300MiB. The collector appears to loop through repeated full shard-list
  passes rather than exiting after one (each "DEX swaps collection complete" cycle still writes substantial new rows —
  139,860 this pass — meaning it's not yet fully fresh/converged); this is presumably bounded to terminate once a pass
  yields near-zero new writes. No preemptions since 02:38 UTC.

- **2026-07-23 04:33 UTC (dex-swaps preempted a THIRD time — resumed again)** — died ~04:05, confirmed via
  `get-serial-port-output` (not found) + memory trail healthy right up to the last sample (1137MiB/13.4%, no OOM
  signal). Three preemptions in ~10h total elapsed (01:20, 01:43, 04:05) is more frequent than the LST-rates VM saw
  (zero preemptions across its whole ~7.5h run) — plausibly this zone/machine-type combo has elevated SPOT reclaim
  pressure right now, not a code issue (memory has been healthy every single time, and the resume mechanism has now been
  verified working twice). Per CLAUDE.md, switching to on-demand for a backfill is itself the anti-pattern to avoid —
  staying on SPOT + idempotent resume is correct. Relaunched again (same command), all tarballs fresh, RUNNING. Will
  keep resuming through preemptions as needed; flagging the elevated frequency here for visibility, not as an action
  item.

- **2026-07-23 04:54 UTC (dex-swaps preempted a FOURTH time — switched to on-demand, evidence-based exception)** — the
  04:33 relaunch never wrote a single new `run.log` line (`gsutil stat` confirms last update `04:05:49`, i.e. BEFORE
  that relaunch — `TARBALL_PINS.json` updated `04:32:57` confirming the launch did happen, but the VM died before the
  Python process logged anything). Confirmed via `gcloud compute operations list --filter="targetLink~mtds-dex-swaps"`:
  **4 real `compute.instances.preempted` system events**, with time-to-preemption STRICTLY DECREASING each cycle —
  ~7h15m (original launch, no preemption) → resumed, ~17min (1st preemption) → resumed, ~2h22m (2nd) → resumed,
  **~2-3min (3rd, this one)**. This is a genuine, worsening SPOT capacity shortage for `e2-standard-4` in
  `asia-northeast1-c` right now, not "bad luck" — the pattern of decreasing survival time is the tell. Per CLAUDE.md,
  blindly switching to on-demand is normally the anti-pattern to avoid for backfills, but the launcher provides
  `--on-demand`/`ON_DEMAND=true` as an explicit, sanctioned escape hatch for exactly this evidenced class of situation —
  used it for THIS relaunch only, with the reasoning documented here rather than silently normalizing the deviation.
  Relaunched: `launch-mtds-dex-swaps-backfill-vm.sh --start 2023-01-01 --end 2026-07-22 --on-demand`, confirmed
  `PREEMPTIBLE` column empty (standard provisioning) at creation. Expect no further preemptions; will revert future
  backfills to SPOT-by-default (this is a one-run exception, not a standing change).

- **2026-07-23 05:12 UTC (on-demand relaunch confirmed holding)** — `mtds-dex-swaps-backfill` RUNNING ~18min since the
  04:54 on-demand relaunch (already well past the ~2-3min the last SPOT attempt survived), fresh log activity, RSS
  healthy ~982-1258MiB. The on-demand switch resolved the rapid-preemption issue as expected. Continuing to monitor at
  the normal cadence.

- **2026-07-23 05:43 UTC (dex-swaps re-check — healthy, ~48min on-demand uptime)** — RSS stable ~838-1308MiB, manifest
  at 8,552+ entries. Repeated "DEX swaps collection complete" cycles (~7-8min apart) each still write substantial new
  data (60k-115k records/pass, not converging toward zero) — the exact iteration/termination model isn't fully clear
  from logs alone (no per-day date marker like the LST-rates script has), but the VM is genuinely healthy and producing
  real data, not stuck or erroring. Continuing to monitor via the manifest-count progress metric.

- **2026-07-23 06:16 UTC (dex-swaps — measured REAL progress against the manifest, honest ETA + a genuine efficiency
  finding)** — rather than keep inferring progress from log-activity alone, queried the actual PROD
  `_index/availability_index.parquet` directly: **635 of 1,299 target days captured (48.9%)** for
  `dex_swaps`/`dex_pool_swaps` within the `2023-01-01→2026-07-22` range (total corpus incl. pre-existing pre-2023
  history: 1,126 distinct days, 3,020,389 captured rows). Most recently captured days cluster around
  `2024-09-17→2024-09-25` — i.e. genuinely still mid-range, not near the end. Traced the handler code
  (`dex_swaps_handler.py::process()`) — confirmed it IS one real calendar day per invocation (not a whole-range single
  pass as I'd initially assumed), all 24 configured (protocol, chain) shards processed per day. At the observed
  ~7-8min/day cadence, the remaining ~664 days imply **roughly 3.5 more days of continuous runtime** — materially longer
  than the "few more hours" impression from earlier log-activity-only checks. Recording this honestly rather than
  letting an optimistic ETA stand uncorrected. **Genuine efficiency finding (not touched this session — documented for a
  future pass)**: of the 24 configured (protocol, chain) shards, roughly 15 have produced EXACTLY ZERO records in every
  single sampled day across this entire session (`uniswap_v3_BASE`/`OPTIMISM`, all `pancakeswap_v3_*`, all `balancer_*`,
  all `sushiswap_v3_*`, `velodrome_v2_OPTIMISM`, `trader_joe_v2_AVALANCHE`, `uniswap_v4_ETHEREUM`,
  `camelot_v3_ARBITRUM`, `aerodrome_v3_BASE`) — each one cycles through 5-8 cascade-fallback query schemas before giving
  up, EVERY single day, for a subgraph that (per the identical "schema drift"/"bad indexers" errors every time) appears
  permanently dead/unindexed, not transiently down. This wastes a real fraction of each day's ~7-8min cycle on shards
  that will never produce data. Only ~6-7 shards (`uniswap_v3_ETHEREUM/ARBITRUM/POLYGON`, `curve_ETHEREUM/AVALANCHE`,
  `sushiswap_ARBITRUM`, `uniswap_v2_ETHEREUM`) are genuinely live. **Not fixed this session** (would mean editing the
  default protocol list or adding a dead-subgraph skip-list mid-backfill, a real scope decision, not something to make
  unilaterally while a backfill is in flight) — flagging as a real, worthwhile follow-up: pruning/gating the ~15 dead
  shards would meaningfully speed up this and any future `dex_swaps` backfill.

- **2026-07-23 07:10 UTC (dex-swaps — scaled to a 3-VM date-sharded fleet, operator-approved)** — measured the exact
  remaining gap first: 570 contiguous missing days, `2024-10-07 → 2026-07-21` (729/1299 days already captured, no
  scattered gaps — clean contiguous tail). Stopped the single `mtds-dex-swaps-backfill` VM (deleted cleanly) and
  relaunched as 3 on-demand VMs, each covering an even ~190-day chunk with a distinct `SHARD_INDEX` (spreads the
  starting TheGraph key across the shared 9-key pool):
  - `mtds-dex-swaps-backfill-1`: `2024-10-07 → 2025-05-11`, SHARD_INDEX=0
  - `mtds-dex-swaps-backfill-2`: `2025-05-12 → 2025-12-14`, SHARD_INDEX=3
  - `mtds-dex-swaps-backfill-3`: `2025-12-15 → 2026-07-21`, SHARD_INDEX=6 All on-demand (not SPOT) — deliberate, given
    the earlier session's 4-preemption pattern in this exact zone; 3 concurrent on-demand e2-standard-4s for the ~20-30h
    target window is the accepted cost tradeoff for reliability. All 3 confirmed RUNNING at launch, tarballs fresh.
    **Did NOT apply the dead-shard `--protocols` pruning optimization found earlier** — attempted it, but found a real
    bug: the launcher's `--protocols` flag (comma-separated, per its own docs) collides with `gcloud`'s own
    comma-delimited `--metadata` parsing (`Bad syntax for dict arg: [curve]`), so passing more than one protocol breaks
    VM creation entirely. Filed as a quick, low-risk follow-up (fix: either `--metadata-from-file` for this one field or
    gcloud's alternate-delimiter escape syntax) — not blocking, just means all 3 VMs still carry the ~15 known-dead
    shards' retry overhead per day. T+10min verification pending.

- **2026-07-23 07:20 UTC (dex-swaps 3-VM fleet — T+10min confirmed healthy)** — all 3 VMs (`-1`/`-2`/`-3`) RUNNING, RSS
  1200-1270MiB each (healthy), fresh heartbeats and resource samples across all 3. No preemptions.

- **2026-07-26 07:37 UTC (dex-swaps fleet re-check via `defi_satellite_ao_dispatch_batch2-022` — honest slow-pace
  finding, NOT closed)** — all 3 VMs still `RUNNING` (~3d uptime), `run.log` fresh within the last minute on each, none
  vanished. Measured real progress off each VM's small `_index/per_vm/{vm}.parquet` shard (not the ~1GB consolidated
  index — an attempt to re-read that thrashed this dev host's memory under concurrent slot load, killed, redone
  targeted): `-1` 23/217d done (dates touched 2024-11-15..2024-12-07), `-2` only 2/217d (2025-06-02..03), `-3` 35/219d
  (2026-02-26..2026-04-01). None `process_final=True` — checkbox stays unflipped, no false-completion claim.
  **Finding**: `-1`/`-3` average only ~2-3h/calendar-day (~20-70x slower than the pre-split 2026-07-23 ~7-8min/day
  estimate); `-2` is a further ~15-18x slower still (~1.5 wall-clock days/calendar-day), with genuine multi-hour gaps
  between `RESOURCE_SAMPLE` lines overnight 07-25 and 2 recurring non-fatal
  `ManifestFreshnessCache read_availability_index failed` errors — likely TheGraph-key-pool contention now shared 3-way,
  not the already-known dead-shard overhead (common to all 3, doesn't explain `-2`'s extra gap). Not root-caused or
  acted on (out of this todo's verify/relaunch scope) — flagging for next check-in / an operator kill+relaunch call on
  `-2` once understood. Realistic remaining runway: multi-day-to-multi-week, not hours — re-check later, not stalled.

- **2026-07-26 07:56 UTC (corroborating re-check, same task re-dispatched post-compaction)** — all 3 VMs still
  `RUNNING`, `run.log` fresh (VM3 actively writing as of 07:56), no `EXIT_STATUS` on any, none vanished. Manifest entry
  counts climbing (`-1` 79,541, `-2` 3,936, `-3` 196,930 as of this check). Nothing materially changed in the ~19
  minutes since the prior check — confirms it, does not supersede it. Not re-doing the fuller day-count analysis above
  (would be duplicated effort with no new signal this soon). Same verdict stands: not yet closeable.
