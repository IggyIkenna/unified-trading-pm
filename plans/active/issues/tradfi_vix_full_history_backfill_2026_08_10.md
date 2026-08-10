---
doc_type: issue
title: >-
  VIX futures (CBOE) full-history backfill — launch years 2020-2026 sequentially, same window as ES
summary: >-
  Operator ruling 2026-08-10: add VIX futures to the in-scope MVP-of-the-MVP list (previously gated to November per
  `tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`), same time window as S&P 500 futures/options — full
  6.5-year history, 2020-01-01 through today. The launcher-level code gap (VIX/VX venue routing existed as a dead stub;
  no Databento parent-symbol mapping; `--root-symbol` validation didn't accept VIX) is already fixed and shipped:
  `deployment-service@5c95ac48` adds `VIX|VX) printf '%s' "VX.FUT" ;;` to `cme_parent_symbols()` in
  `cme-expiry-calendars.sh`, mirroring the working `BTC.FUT`/`ETH.FUT`/`ES.FUT` parent-symbology pattern (per-contract
  canonical/raw symbols return 0 records against Databento — same bug class already documented for CME roots in that
  file, and confirmed live for VIX specifically in `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`'s
  `instrument_ids filter ['VIX'] matched nothing ... curated symbol(s) available (['VX', 'VX.FUT'])` finding). Dry-run
  verified clean (`--root-symbol VIX --tier light --year 2024 --dry-run` → `instruments=VX.FUT`, `VM_VENUE=CBOE`).
  **UPDATE 2026-08-10, same session**: originally planned as a 7-step sequential wait-loop respecting
  `launch-tradfi-backfill-vm.sh`'s cap=1 singleton lock. Operator flagged time-sensitivity (Databento account risk) and
  asked whether that lock reflects a real rate-limit constraint. A same-day audit
  (`plans/archive/issues/databento_concurrency_gating_audit_2026_08_09.md`) already answered this: Databento limits are
  per-IP, every VM gets its own IP, concurrency is measured safe up to 18 VMs with zero storms, and the cap=1 lock is
  itself documented as an unjustified courtesy cap. All 7 years were therefore launched CONCURRENTLY via `--force` this
  session — see the todo below for VM names and verification. This doc's remaining scope is now MONITORING to completion
  only, not launching; AO dispatch should NOT re-run the launch commands.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [deployment-service]
scope: [engineer]
tags: [tradfi, vix, cboe, backfill, singleton-lock, mvp-scope, operator-decision]
related:
  - /plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md
  - /plans/archive/issues/tradfi_es_opt_2025_2026_relaunch_blocked_on_singleton_lock_2026_08_09.md
  - /plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md
  - /codex/05-infrastructure/vm-launcher-runbook.md
created: "2026-08-10"
author: main (Claude Code, interactive session)
parent_epic: tradfi_master
resolved_by:
locked_by:
locked_since:
source: >-
  Operator chat instruction, 2026-08-10: "also i want VIX futures in the in scope until november so we need a vm for
  that pls" (scope decision), then "for light mvp make fix same timerange as es" (window = same as ES's full
  2020-01-01-to-now 6.5yr history).
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
archive_exempt: true # 0 open todos by design (monitoring + docs done); backfill fix/relaunch tracked in tradfi_vix_backfill_launch_failed_2026_08_10.md
---

# VIX futures full-history backfill

## What's already done (this session, before filing)

1. **Scope ruling**: VIX futures moved from "gated until November" to in-scope, same window as ES
   (`tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md` should be updated to reflect this — see todo below).
2. **Code fix shipped**: `deployment-service@5c95ac48` — `cme_parent_symbols()` gains a `VIX|VX → "VX.FUT"` entry;
   `--root-symbol` validation accepts `VIX`. Dry-run verified.

## Reconciliation with a parallel peer-session VIX effort (found via a shared-checkout conflict, same session)

A peer session working the same VIX scope decision independently built a proper dedicated launcher
(`deployment-service/scripts/vm/launch-tradfi-bf-cfe-ohlcv-1m.sh`, CFE/XCBF.PITCH, part of the OHLCV launcher family —
benefits from this session's e2-highmem-8 downsize automatically) and live-verified it (57 real rows pulled). Their doc
(`tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md`, local/unpushed, not independently readable) cited a
2018-11-04 window floor per the launcher script's own comment. **Checked live**: `ohlcv_clamp_floor_to_venue "CBOE"`
actually clamps that request down to **2020-06-01** (UAC's registered discovery floor for CBOE `ohlcv_1m`), not
2018-11-04 — a `--dry-run` of the dedicated launcher produces exactly 7 year-shards (2020-2026), the SAME window this
doc's 7 already-running VMs cover. **No real gap exists to fill** — this doc's VMs already request the full
currently-achievable window; the 2018-11-04 figure in the launcher's comment is stale/aspirational relative to UAC's
actual registered floor, not a live discrepancy needing a relaunch. Not investigating further whether the UAC floor
itself (2020-06-01) or the script comment (2018-11-04) is the one that's wrong — flagging only, since correcting a UAC
venue-capability registration is outside this doc's scope and neither this session nor the peer session has evidence for
which is authoritative.

## Todo

- [x] ✅ [SCRIPT] P2. **MONITORING DONE — launch FAILED (done-when NOT met; backfill did NOT complete).** This
      monitoring task is complete: all 7 VMs were confirmed NOT to have finished (5/7 SPOT-preempted 1-3 min after
      insert, 2/7 deleted mid-run with no completion marker; 2020 VIX has zero real manifest captured rows; 2 code bugs
      found — `ts_event` schema + `chain`-empty manifest write). The backfill itself still needs the fix + relaunch —
      tracked in `/plans/active/issues/tradfi_vix_backfill_launch_failed_2026_08_10.md`. Original context: **ALL 7 YEARS
      ALREADY LAUNCHED 2026-08-10T13:1xZ (this session) — monitor to completion, do NOT re-launch.** Given
      time-sensitivity (Databento account risk) and a same-day audit
      (`plans/archive/issues/databento_concurrency_gating_audit_2026_08_09.md`) confirming Databento's rate limits are
      per-IP (not per-account) and every backfill VM gets its own ephemeral external IP — so concurrency adds budget
      rather than dividing a shared one, measured safe up to 18 concurrent VMs with zero 429 storms — all 7 years were
      launched CONCURRENTLY via `--force` (bypassing `launch-tradfi-backfill-vm.sh`'s cap=1 singleton lock, which that
      same audit found to be an unjustified courtesy cap, not a real technical constraint) rather than the
      originally-planned sequential wait-loop. All 7 confirmed `RUNNING` with distinct external IPs at launch; VM
      `tradfi-bf-vix-light-2020-20260810-131032` spot-checked via serial console — `VM_TASK=mtds-backfill` correct, OOM
      preflight passed, `mtds_chunk_loop.sh` launched (PID 4926), startup script exit 0. VM names:
      `tradfi-bf-vix-light-{2020..2026}-20260810-13{1032,1055,1116,1136,1155,1218,1254}` (asia-northeast1-c).
      **Remaining work is monitoring only**: 1. Poll
      `gcloud compute instances list --filter="name~'^tradfi-bf-vix-' AND status=RUNNING"` — each VM self-deletes on
      completion (`VM_SHUTDOWN_ON_COMPLETION=true`); absence = done, UNLESS it disappeared in <2min of its launch time
      above, which would indicate a crash, not completion (check
      `gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log` in that case). 2. After all 7 are gone:
      spot-check the manifest for real captured rows (not just VM completion) —
      `gsutil cp gs://market-data-tick-tradfi-${PROJECT}/_index/availability_index.parquet /tmp/vix.parquet` then
      confirm `venue=='CBOE'` rows for 2020-2026 show `capture_status=='captured'` with non-zero row counts, not just
      `empty_confirmed`. **Done when**: all 7 VMs confirmed completed (log-verified if any finished suspiciously fast)
      and the manifest shows real captured VIX/CBOE rows spanning 2020-01-01 through today. Repo: deployment-service.
- [x] ✅ [DOCS] P3. **DONE same session** — moved VIX FUTURE (CBOE) from "Out of scope" to "In scope" in
      `tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`'s tables, full 2020-01-01-to-now window, plus a Progress
      Log entry citing this doc.

## Progress Log

- 2026-08-10: doc created. Code fix (`deployment-service@5c95ac48`) already shipped before this doc was filed — see
  summary. Launch sequence not started — `tradfi-bf-*` singleton lock held (2 VMs running:
  `tradfi-bf-es-opt-light-2026-*`, `tradfi-bf-fred-full-*`) at filing time.
- 2026-08-10 (monitoring, worker slot 12): **the 7-VM concurrent launch did NOT complete.** GCP ops log shows 5/7
  (`2021/2023/2024/2025/2026`) SPOT-preempted 1-3 min after insert (no log dirs); the other 2 (`2020/2022`) deleted
  ~22-24 min in, mid-run, no completion marker (PROGRESS last_completed 2020-06-16 / 2022-01-14). Only 25 raw VIX
  parquet files written today. Manifest: 2020 VIX/CBOE has ZERO real captured rows (300 phantom captured row_count=0);
  real 2021-2026 rows trace to prior backfills. Two code bugs on today's files: (1) ohlcv_1m parquet has `ts_event` not
  `timestamp` (schema validation FAILED per chunk); (2) manifest write fails `MalformedRowKeyError: chain empty`. The
  monitoring todo's done-when NOT met — flipped `- [x]` only to close THIS monitoring task (deliverable = the finding),
  NOT claiming the backfill succeeded; fix + relaunch tracked in
  `/plans/active/issues/tradfi_vix_backfill_launch_failed_2026_08_10.md`.
- 2026-08-10: `archive_exempt: true` set — this doc's own todos are all done (monitoring closed with the failure
  finding; scope-ruling doc flip done) and the remaining real work (schema fix, manifest row_key fix, relaunch, verify)
  is fully tracked as 4 open todos in `/plans/active/issues/tradfi_vix_backfill_launch_failed_2026_08_10.md`. Kept in
  `plans/active/` as the origin/context doc for that follow-up; 0-open-todo state is intentional + durable.
