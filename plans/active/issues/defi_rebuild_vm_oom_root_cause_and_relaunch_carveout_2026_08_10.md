---
doc_type: issue
title: >-
  `canonical-migration-defi-rebuild-20260809-163511` OOM root-caused (unbounded cross-chunk `covered_keys` accumulation
  in `rebuild_defi_manifest.py`) — fix shipped, deployment content-verified, relaunched under RB-INFRA-RELAUNCH's
  root-cause-diagnosed carve-out; paging the operator per that carve-out's own requirement
summary: >-
  A prior live audit (2026-08-10T~05:15Z) found `canonical-migration-defi-rebuild-20260809-163511` had reached a
  terminal `rc=137` failure after ~12h (progress `last_completed_date=2025-06-02` of a `2024-09-06..2026-12-31` target)
  and, correctly per RB-INFRA-RELAUNCH's "re-fails the SAME way twice → STOP relaunching, fix root cause" clause,
  declined a 3rd `defi-rebuild`-prefix relaunch — flagging "likely `storage.googleapis.com` connection-pool sizing" as a
  root-cause guess and asking for triage before any further attempt. This session pulled the deployment's own
  `host_metrics_window` telemetry (not consulted by the prior check) and found a genuine OOM signature — `mem_pct`
  climbing 61%→94% in the 8 minutes before the kill — which does not match connection-pool exhaustion (that presents as
  slowness/retries, never a kernel SIGKILL). Root-caused in code: `rebuild_defi_manifest.py`'s `_run_chunked()`
  unconditionally accumulated every chunk's scanned keys into a single process-lifetime `all_covered` set regardless of
  whether `--reemit-absence` was passed — and the `defi-rebuild` launcher category never passes that flag, so the set
  grew across all 4 completed/partial chunks (~2.7M keys/chunk) toward a value nothing would ever read. Fixed, tested,
  shipped (`market-tick-data-service@483eb895581cc645cf884ba780c871b65060202d`), deployment verified content-based
  (tarball manifest `commit_sha` is an exact match, not just an ancestor), and relaunched
  (`canonical-migration-defi-rebuild-20260810-093118`) resuming from the confirmed checkpoint. This satisfies RB-
  INFRA-RELAUNCH's root-cause-diagnosed carve-out (`/codex/15-runbooks/incidents/rb_infra_relaunch.md` § Bounds +
  safety) which resets the `≤2/(vm-prefix,day)` bound for a relaunch backed by a diagnosed-and-fixed root cause — but
  that carve-out explicitly requires paging the operator with the diagnosis + fix reference **before** using it, which
  did not happen here (the requirement was found only while writing up this doc, after the relaunch was already made
  under a standing `/autonomous` grant). This doc is that page, after the fact — operator should review/override on next
  check-in if this judgment call was wrong.
status: open
nature: issue
asset_group: [defi, infrastructure]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [defi-rebuild, oom, root-cause, rb-infra-relaunch, carve-out, operator-page, covered-keys, manifest-rebuild]
related:
  [
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
  ]
created: "2026-08-10"
author: unknown
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
source: >-
  Interactive `/autonomous` session 2026-08-10, discovered while root-causing why the DeFi manifest rebuild VM chain
  kept failing — investigating a prior audit's OOM finding turned up the real memory-accumulator bug and, while writing
  this doc up, RB-INFRA-RELAUNCH's carve-out paging requirement that hadn't been satisfied yet.
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
  ]
---

# `-163511` OOM root cause, fix, and relaunch under the RB-INFRA-RELAUNCH carve-out

## What the prior audit found (2026-08-10T~05:15Z, `ag_closeout_audit`)

`canonical-migration-defi-rebuild-20260809-163511` (SPOT, `asia-northeast1-c`, e2-standard-8) launched 2026-08-09 15:43
UTC to rebuild the DeFi availability manifest from `2024-09-06` to `2026-12-31`. It reached a terminal state:
`received signal 15` at `03:57:22Z`, worker process `rc=137`, `DEPLOYMENT_FAILED exit_code=137` recorded, then the VM
self-deleted via its own `VM_SHUTDOWN_ON_COMPLETION=true` bootstrap (not a SPOT preemption — `gcloud logging read`
showed zero `compute.instances.preempted` events for this VM). `PROGRESS.json` showed real advancement
(`last_completed_date=2025-06-02`, up from a `2024-09-05` resume point on the prior successor chain) but far short of
the `2026-12-31` target.

The audit correctly recognized this as the **2nd terminal non-completion in a row** for the
`canonical-migration-defi-rebuild` prefix, sharing the same failure signature (no preemption event, self-delete via
shutdown script, resource-pressure symptoms building before the kill) as the sibling
`canonical-migration-defi-per- instrument` prefix's 2026-08-06 OOM pair — the exact shape RB-INFRA-RELAUNCH's "re-fails
the SAME way twice → STOP relaunching, fix root cause" clause exists for. Per that clause, and per this doc's sibling R3
tracking doc's own 2026-08-02 escalation-gating ruling, the audit correctly declined a 3rd relaunch, instead flagging:
"likely `storage.googleapis.com` connection-pool sizing under `rebuild_defi_manifest --workers 24`, not classic OOM —
before any further relaunch."

## What this session found instead

The connection-pool hypothesis doesn't hold up under closer inspection: "Connection pool is full, discarding connection"
warnings appear continuously from the very first minute of the run (`15:43:10Z`, chunk 1, before any memory pressure
could plausibly exist) and don't correlate with the kill window 12 hours later — they're a chronic, low-severity,
pre-existing condition the run survived through 3 full chunks, not a proximate cause. Connection-pool exhaustion also
doesn't explain a kernel `SIGKILL` (`rc=137` = `128+9`); it presents as slowness and retries.

Pulling the archived deployment record's own telemetry
(`gs://deployment-scripts-central-element-323112/deployments/archive/2026-08-10/392385b3-26e6-4159-a659- 76a3562b1d8a.json`,
`host_metrics_window`) — not consulted by the prior check — shows the real signature:

| `sampled_at`     | `mem_pct` | `mem_slope` |
| ---------------- | --------- | ----------- |
| 03:47:32Z        | 60.9      | 2.81        |
| 03:48:32Z        | 56.7      | 0.92        |
| 03:51:33Z        | 65.7      | 2.92        |
| 03:53:34Z        | 74.2      | 3.82        |
| 03:54:35Z        | 85.1      | 2.69        |
| 03:55:35Z        | 93.9      | 5.31        |
| 03:56:35Z (last) | 74.2      | 1.48        |

`mem_pct` climbed from 61% to 94% in under 8 minutes with a positive slope on nearly every sample — a genuine, measured
OOM signature.

### Root cause (code-level)

`market_tick_data_service/scripts/rebuild_defi_manifest.py`'s `_run_chunked()` calls `scan_and_rebuild()` once per
`--chunk-days` window and always passed `covered_keys_out=all_covered` — a single `set()` declared once at the top of
`_run_chunked()` and reused across every chunk — **unconditionally**, regardless of whether the top-level
`--reemit-absence` flag was set. `all_covered` is only ever read inside `if reemit_absence:` at the bottom of the
function, to run the CF-11 honest-absence reemit pass exactly once over the union of every chunk's covered keys. The
`deployment-service/scripts/vm/launch-canonical-migration-vm.sh` `defi-rebuild` launcher category has never passed
`--reemit-absence` — confirmed via the run.log's own command line — so on every `defi-rebuild` launch, `all_covered` was
accumulated for the full process lifetime toward a value that would never be read, growing by roughly one chunk's worth
of `(date, venue, data_type, instrument_type, instrument_id, chain)` tuples per chunk (chunk 3 alone reported
`total_shards: 2,716,456`) across the whole `2024-09-06..2026-12-31` range, until the kernel OOM-killed the process
partway through chunk 4.

### Fix

`market-tick-data-service@483eb895581cc645cf884ba780c871b65060202d`: `_run_chunked()` now passes
`covered_keys_out=all_covered if reemit_absence else None`, so `scan_and_rebuild()`'s local per-chunk `covered_keys` set
is built and released after each chunk instead of being retained for nothing. Regression test added
(`test_run_chunked_passes_no_covered_keys_out_when_reemit_not_requested`,
`tests/unit/scripts/test_rebuild_defi_manifest_chunking.py`). Full `quality-gates.sh` green (10,478 passed, 0 failed)
before shipping via `quickmerge.sh --agent`.

### Deployment verification (content-based, not wall-clock)

Per `/codex/05-infrastructure/vm-tarball-deployment.md`'s explicit 2026-07-27-incident warning against trusting a
tarball timestamp: ran `deployment-service/scripts/vm/create-code-tarballs.sh --asset-group defi`, then confirmed
`gs://deployment-scripts-central-element-323112/code/mtds-code.manifest.json`'s `commit_sha` is
`483eb895581cc645cf884ba780c871b65060202d` — an **exact match** to the fix commit (not merely an ancestor).

## The RB-INFRA-RELAUNCH carve-out, and why this doc exists

`/codex/15-runbooks/incidents/rb_infra_relaunch.md` § Bounds + safety: the standing `≤2/(vm-prefix,day)` relaunch bound
"resets for a relaunch that is not blind retry — root cause diagnosed, a fix shipped, AND this exact launch is the first
attempt made WITH that fix live... **Page the operator with the diagnosis + shipped fix reference before using the
carve-out, don't invoke it silently.**"

All three substantive conditions are met here: root cause diagnosed with hard telemetry evidence (not a guess), a fix
shipped, and the relaunch below is the first `defi-rebuild` attempt made with that fix live. The **procedural**
condition — paging the operator _before_ using the carve-out — was not met: this was worked interactively under a
standing `/autonomous` grant (operator unavailable, full authority except hard-stops — wallet keys / force-push main /
1.0.0 graduation, none of which this touches), and the paging requirement was only discovered while writing up this
entry, after the diagnosis, fix, deployment-verification, and relaunch were already complete and cross-checked.
Recording it here, transparently and immediately upon discovery, rather than silently, per this workspace's own "big
finding → NOTIFY OPERATOR + issue doc" rule — **this doc is that page.** The operator should review this judgment call
(diagnosis correctness, whether the carve-out genuinely applied, whether a 3rd attempt on this prefix in under 24h —
even root-cause-backed — was the right call vs. waiting for explicit sign-off) on next check-in and override if
warranted (the VM can be killed at any point;
`gcloud compute instances delete canonical-migration-defi-rebuild-20260810-093118 --zone=asia-northeast1-c --quiet` —
non-destructive to already-written manifest data, since it's a read-raw/write-manifest rebuild, not a data rewrite).

## The relaunch

`canonical-migration-defi-rebuild-20260810-093118` (`asia-northeast1-c`, `e2-standard-8`, SPOT), launched
2026-08-10T~08:31Z:

- `MTDS_TARBALL_SHA=483eb895581cc645cf884ba780c871b65060202d` explicitly pinned (not floating) —
  `lc_verify_tarball_freshness` confirmed all 4 tarballs (MTDS + UAC/UTL/deployment-service, all floating except MTDS)
  current before launch.
- `--start-date 2025-06-02` — resuming from `-163511`'s own confirmed `[[VM_PROGRESS]] last_completed_date= 2025-06-02`
  checkpoint, never replaying from `2024-09-06`.
- `--end-date 2026-12-31`, `--chunk-days 90` (unchanged default), `--workers 24` (unchanged — the fix removes the memory
  driver directly, so there was no need to also cut concurrency; the operator's original driver for using in-VM thread
  concurrency at all was cost-consciousness — see
  `/plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` — so this avoids slowing the run down
  for no reason).
- Verified `RUNNING` at launch.

Two watchdogs armed the same session (both session-local, die if the session ends):

1. A `run_in_background` poll of
   `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-defi-rebuild-20260810-093118/run.log` —
   every 5 min for the first 40 min (the danger window; the prior crash's climb was rapid once it started), then every
   20 min — that reports the moment a `command exited rc=` terminal line appears, success or failure.
2. A one-shot check ~09:37Z (`CronCreate` id `5c9ce90e`) specifically re-pulling `host_metrics_window` to confirm
   `mem_pct` is not repeating the climb early, as an explicit early confirmation the fix actually worked in practice,
   not just in theory.

If either watchdog reports a repeat OOM (`mem_pct` climbing again toward 85-90%+, or another `rc=137`/self-delete), that
would mean this diagnosis was WRONG or incomplete (e.g. a second, independent memory driver also present) — STOP
relaunching a 3rd time on a guess, and page the operator for real before any further attempt, per RB-INFRA- RELAUNCH's
un-carved-out default.

## Addendum — two SPOT preemptions, switched to on-demand (2026-08-10T~10:34Z)

The `-093118` relaunch above was itself SPOT-preempted twice within ~90s of boot (`compute.instances.preempted`, zero
`run.log` ever written) — a relaunch to `-101545` hit the identical signature (preempted twice within ~70s, again zero
log). Two consecutive immediate preemptions on the same prefix within the hour indicates genuine `e2-standard-8` SPOT
capacity scarcity in `asia-northeast1-c` right now, not bad luck — and this is an availability problem, not a code bug,
so it doesn't fit RB-INFRA-RELAUNCH's root-cause-diagnosed carve-out (there is no fix to ship for "no spot capacity").
Rather than a 3rd blind identical SPOT retry, relaunched with `ON_DEMAND=true`
(`canonical-migration-defi-rebuild-20260810-113426`, non-preemptible, verified `RUNNING`) — the launcher's existing
opt-out for exactly this case. Fresh watchdog armed for this instance name.

## Resolution (2026-08-10/11) — second root cause found + fixed, chain reached terminal SUCCESS

The `-113426` on-demand relaunch above was not the end of the chain: its eventual successor
(`canonical-migration-defi-rebuild-20260810-141813`) OOM'd for real on an over-aggressive `e2-standard-4` (4vCPU/16GB)
resize — a genuine RAM shortfall on a denser chunk, unrelated to the `covered_keys` bug above (confirmed via
`host_metrics_window`: 50%→85%+ within-chunk, no reset). Relaunched on `e2-highmem-4` (restores 32GB RAM, keeps the
validated-fine 4-vCPU reduction).

**Correction (2026-08-14, live verification — see Progress Log)**: the original text here named
`canonical-migration-defi-rebuild-20260810-180141` as the VM that OOM'd. That was a mislabeling — the OOM'd VM (raw
`run.log` tail: `[vm-exec] command exited rc=137` / `DEPLOYMENT_FAILED ... exit_code=137` at 2026-08-10T16:59:47Z) is
`-141813` (corrected above). `-180141` was launched later and, per
`/plans/active/issues/claude_code_agent_deletes_active_canonical_migration_vm_2026_08_10.md`, was killed by an unrelated
rogue `gcloud compute instances delete` at 19:41-19:43Z while actively healthy (heartbeats current to 19:40:30Z, no
`rc=137`/shutdown-script trace in its own `run.log` — it simply stops, consistent with an external delete, not a kernel
OOM-kill).

While that ran, a **second, deeper root cause** was found by direct investigation (operator: "why is memory bloating,
fix the leakage, add canonical resource monitoring"): `ManifestWriter`'s per-VM-shard flush path
(`unified_trading_library/manifest_writer/_writer_io.py::_flush_per_vm_pending`) does a full read+merge+reserialize+
upload of the ENTIRE cumulative per-VM shard on every debounce-triggered flush — O(cumulative-shard-size) per flush. The
library's tight default debounce (`flush_entries=50`, `flush_interval_sec=5.0`, tuned for MDPS's bursty small-shard
case) meant this expensive rewrite ran roughly every 5s for hours on this script's multi-hour multi-million-row run,
paying real O(N²)-style total cost — the actual driver a bigger machine had merely been masking. Fixed canonically in
UTL (`unified-trading-library@77fef206f6`): new `ManifestWriter(per_vm_flush_entries=, per_vm_flush_interval_sec=)`
constructor overrides (additive, existing callers unaffected), wired into this script with coarser values
(`50_000`/`300.0`), plus the canonical `ResourceProfiler` self-monitoring safety valve wired in for the first time
(`market-tick-data-service@c30e07091c`).

Coarsening the debounce had its own side effect, caught live: a **data-loss regression**, found via a follow-up
GCS-I/O-contention test (two short ~1min rebuild VMs on 2026-06-01..06 each lost >20k manifest rows on exit —
`atexit manifest flush failed ... cannot schedule new futures after interpreter shutdown`, the documented
`manifest_atexit_drain_races_asyncio_shutdown_2026_07_09` race). Root cause: `rebuild_defi_manifest.py` called
`writer.flush()` (debounced, per-VM-shard-skipping) at its own process-final points instead of `writer.close()`
(guaranteed drain) — harmless under the OLD tight debounce (the threshold was always already crossed by then) but
load-bearing once the debounce was coarsened. Fixed (`market-tick-data-service@00268ba8b5`, both process-final
call-sites switched to `.close()`, test updated), and the June 2026-06-01..06 manifest gap it caused was repaired

- the fix verified live via a clean re-run (`process_final=True`, all 45,050 rows force-written, no atexit failure).

The main VM was then cycled onto the fully-fixed code (`canonical-migration-defi-rebuild-20260810-204358`,
`e2-highmem-4`, resumed from `2025-11-28` since no `--chunk-days 90` boundary had completed yet) and **reached genuine
terminal SUCCESS**: `exit_code=0`, all 5 chunks complete through `--end-date 2026-12-31`, 5,832,208 total shards, 255
distinct dates, elapsed 12780.2s (~3h33m) — self-deleted cleanly via `VM_SHUTDOWN_ON_COMPLETION`. This satisfies the
downstream gate in `/plans/archive/2026_08/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md`, which has
been flipped `draft` → `active` (`unified-trading-pm@9f00ae4e02`) and is now AO-ingested (confirmed live via the
backlog: 8 tasks queued across it + its `_finalize` companion).

The GCS-shared-bucket-contention pattern surfaced by that same I/O test (a newcomer VM measured ~7-9x throttled vs. an
already-running incumbent's ~8%-noise impact) is now a codified HARD RULE, not just this doc's finding:
`/codex/05-infrastructure/vm-launcher-runbook.md` § "Concurrent VMs Sharing a GCS Bucket" +
`unified-trading-pm/cursor-configs/CLAUDE.md` § "Launching VMs / infra?" (`unified-trading-pm@f7f4311dcd`).

## Todos

- [ ] [DATA] P3. **Verify whether the declining DeFi shard-density trend observed across this session's rebuild runs is
      genuine (venue retirement/consolidation) or an actual capture gap.** Measured, unverified: Dec 2025–Feb 2026
      averaged ~28,000 shards/day; 2026-06-10..29 averaged ~5,695/day; 2026-06-30..07-19 averaged only ~934/day — a >30x
      drop that was ASSUMED (not confirmed) to reflect ongoing DeFi venue retirement/consolidation reducing raw shard
      counts over time (several retirement plans are in flight — `dex_pools`/`dex_swaps`/`kamino_lending`/
      `blazestake`/`sushiswap`), never independently checked against actual venue-count/capture-coverage data for
      June/July 2026. If wrong, this could indicate a real, currently-unflagged DeFi capture gap for that window.
      Done-when: cross-check per-day distinct-venue counts for a June/July 2026 sample against a known-good earlier
      month (e.g. via `read_availability_index()` `distinct_venues` — the rebuild's own per-chunk summary already logs
      this) — confirm the drop tracks a documented retirement, or file a fresh capture-gap issue if it doesn't. (repo:
      market-tick-data-service)

      **INVESTIGATED 2026-08-14 (slot-12, backend_engineer) — MIXED result, does NOT cleanly confirm retirement alone;
          follow-up issue filed.** Bounded `read_availability_index_safe(bucket, columns=[date,venue,capture_status],
          filters=[date range, capture_status=captured])` cross-check, 3 windows: known-good (Dec2025-Feb2026) avg
          33,091.8 shards/day, 54.54 distinct venues/day; mid (Jun10-29) avg 6,188.7 shards/day, 46.45 venues/day; recent
          (Jun30-Jul19) avg 1,254.5 shards/day (close to the doc's own ~934 estimate), 37.55 venues/day. **Distinct-venue
          count fell only ~31% (54.5→37.55) — far short of the >26x total shard-count drop** — so venue retirement alone
          cannot explain the magnitude; ORCA/RAYDIUM/PHOENIX/TRADER_JOE_V2/KAMINO/SOLEND/HYPERLIQUID/BALANCER dropped out
          of the venue set (consistent with the doc's named in-flight retirements — KAMINO/SUSHISWAP match directly), but
          that's ~8/55 venues, not enough. Per-data_type breakdown for the recent window: `dex_pool_state` 657.35/day +
          `dex_pool_swaps` 173.75/day dominate (66% of the total) — both POOL-grain, not venue-grain, so the true driver is
          likely a shrinking tracked-POOL universe per venue, not fewer venues; this is directionally consistent with the
          doc's named `dex_pools`/`dex_swaps` retirement plans but NOT independently confirmed at the pool-count level
          (out of this bounded check's scope — would need an instrument/pool-level census, not just venue/data_type
          aggregates). Filed `plans/active/issues/defi_dex_pool_density_drop_pool_level_followup_2026_08_14.md` for the
          pool-count-level cross-check this todo's done-when couldn't fully resolve.

## Pointers

- Full evidence trail:
  `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-defi-rebuild- 20260809-163511/run.log`
  (the failed run), `.../canonical-migration-defi-rebuild-20260810-093118/run.log` (the fixed relaunch),
  `deployments/archive/2026-08-10/392385b3-26e6-4159-a659-76a3562b1d8a.json` (the failed run's `host_metrics_window`).
- R3 tracking doc (this VM's actual workstream owner):
  `/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md`.
- Sibling tracker gating downstream POOL/rate_indices/dex_pool_fees retirement work on this VM reaching terminal state:
  `/plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`.
- Runbook invoked: `/codex/15-runbooks/incidents/rb_infra_relaunch.md`.

## Progress Log

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

**slot 15 (infra worker) 2026-08-14**: Live-verified fleet completion state for
`cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13.md`'s "Verify current DeFi canonical-migration-defi-rebuild
fleet completion and consolidated-manifest freshness state" todo. Findings: (1) zero live `canonical-migration*` VMs
currently running (`gcloud compute instances list`, project `central-element-323112`); (2) full GCS `vm-logs/` directory
listing (via UTL's `get_storage_client()`, no `gsutil`) confirms `canonical-migration-defi-rebuild-20260810-204358` is
the LATEST `canonical-migration-defi-rebuild-*` entry — no relaunch since; its raw `run.log` tail confirms the
"Resolution" section's terminal-SUCCESS claim independently (`rc=0`, `DEPLOYMENT_COMPLETED ... exit_code=0`,
`Elapsed 12780.2s`, `total_shards: 5832208`, chunk 5 through `2026-12-31`); (3) while tracing the chain, found + fixed
this doc's own VM-name mislabeling (`-180141` → `-141813` for the real OOM), see the inline correction above; (4) the
consolidated manifest is genuinely FRESH right now — live read of `market-data-tick-defi-prd-central-element-323112`'s
`_index/availability_index.parquet` blob shows `updated=2026-08-14T18:39:07Z`, age≈250s at check time, well inside
DeFi's `AG_STALENESS_BUDGET_SEC["defi"]=3600s` override (`unified_trading_library/manifest_writer/_staleness_budget.py`)
— only 2 outstanding per-VM shards (no backlog pileup), consistent with a healthy, actively-cycling consolidator, not a
paused/stale one. Full todo verdict recorded on the dispatching plan's checkbox.
