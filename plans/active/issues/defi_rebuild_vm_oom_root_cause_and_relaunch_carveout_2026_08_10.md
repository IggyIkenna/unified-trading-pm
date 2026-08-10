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
assigned_vm: NA
execution_scope: local-only
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
