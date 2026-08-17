---
doc_type: issue
title: UPBIT CeFi data gap — zero captured objects since 2026-05-25 for a codex-MVP venue
summary: >-
  UPBIT is codex-MVP (MVP_SCOPE.cefi.venues, spot-without-perp carve-out) but has produced ZERO captured tick-data
  objects in GCS since 2026-05-25 (~72 days as of 2026-08-04). Prior coverage (2021-03-03 through 2026-05-22) averaged
  ~600 trades+book_snapshot_5 parquet objects/day via batch_tardis. The Tardis backfill stopped abruptly — last full day
  2026-05-22 (606 objects), residual KRW-only book_snapshot_5 on May 23-24 (36 objects/day), then nothing. Live WS
  connectors exist in code but produce no GCS objects. No open issue or backfill plan tracks this gap; the parent plan's
  audit trail has zero UPBIT mentions.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [upbit, cefi, data-gap, mvp, tardis, coverage]
related:
  - /plans/archive/2026_07/cefi_consolidated_native_ao_extract_2026_07_25.md
  - /plans/active/cefi_consolidated_closeout_2026_07_18.md
  - /codex/02-data/mvp-scope-canonical.md
created: "2026-08-04"
author: slot-6 (data_engineering)
source:
  - cefi_consolidated_native_ao_extract_2026_07_25.md (Todo 6 — UPBIT live-wiring confirm)
assigned_vm: planning
parent_epic: cefi_master
resolved_by:
locked_by:
priority: P1
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope:
  [
    deployment-service/deployment_service/calculators/shard_distribution.py,
    deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh,
    /codex/02-data/mvp-scope-canonical.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    configs/data-providers.yaml,
  ]
---

# UPBIT CeFi data gap — zero captured objects since 2026-05-25

## What I found

UPBIT is codex-MVP (`MVP_SCOPE.cefi.venues`, `/codex/02-data/mvp-scope-canonical.md` § CeFi venues row —
spot-without-perp carve-out via `STAKING_SPOT_EXCEPTION`) but has produced **ZERO captured tick-data GCS objects** since
2026-05-25, a gap of ~72 days (as of 2026-08-04) for a venue the MVP definition expects to be live-wired.

**Measured GCS evidence** (read-only, prod buckets, 2026-08-04):

| Metric                        | Value                                                                                                   |
| ----------------------------- | ------------------------------------------------------------------------------------------------------- |
| IS catalogue (day=2026-08-03) | 488 active SPOT_PAIR instruments, 308 base assets, KRW+USDT quotes                                      |
| Pipeline mode                 | `batch_tardis` only — no live/forward mode                                                              |
| Data types captured (pre-gap) | `trades` (~263/day) + `book_snapshot_5` (~345/day) = ~608 obj/day                                       |
| Coverage period               | 2021-03-03 → 2026-05-22 (~5.2 years)                                                                    |
| May 23–24, 2026               | 36 obj/day — KRW-pair book_snapshot_5 ONLY (BTC-KRW, ETH-KRW, DOT-KRW, etc.), no trades, no USDT pairs  |
| **May 25, 2026 → present**    | **ZERO objects** — 72+ day complete gap                                                                 |
| Live WS connectors            | Present in code (`upbit_spot_ws.py`, `upbit_book_ws.py`, `upbit_adapter.py`) but produce no GCS objects |

**Per-day object counts (GCS `raw_tick_data/by_date/`):**

```
2026-05-19: 608 objects  (trades 263 + book_snapshot_5 345)  ← last full day
2026-05-20: 590 objects
2026-05-21: 589 objects
2026-05-22: 606 objects                                      ← last day with trades
2026-05-23:  36 objects  (book_snapshot_5 only, KRW pairs)   ← trades drop
2026-05-24:  36 objects  (book_snapshot_5 only, KRW pairs)
2026-05-25:   0 objects  ← COMPLETE STOP
...
2026-08-04:   0 objects
```

**Known historical issues** (both resolved, `cefi_venue_backfill_coverage_remediation_2026_05_27.md`):

- UPBIT Tardis CSV type mismatch (ArrowInvalid float-in-int-column) — ✅ fixed
- Cross-date memory accumulation (~78 GB) — ✅ fixed

Neither explains the May-25+ gap.

## Why it matters

1. **MVP definition breach**: UPBIT is explicitly listed as an MVP venue with no known caveats or deferred status. A
   codex-MVP venue with zero data for 2.5+ months is a material gap in the honest-coverage denominator.
2. **Invisible to the audit surface**: The parent `cefi_consolidated_closeout_2026_07_18.md` plan has zero UPBIT
   mentions — this gap has never been triaged or tracked. The `cefi_master.md` epic expects UPBIT at
   "trades/book_snapshot_5, 450 each."
3. **Root cause unknown**: Is Tardis UPBIT data simply unavailable past May 2026 (vendor-side ceiling — then UPBIT needs
   a non-Tardis source or MVP descope), or did the pipeline silently stop (then it needs a VM restart/repair)?
4. **Live connectors don't close the gap**: The WS connectors exist in code but produce no GCS objects — the only data
   source is the Tardis backfill, which is what stopped.

## Recommended decision

1. **Diagnose root cause first** — check whether Tardis actually carries UPBIT data past May 2026 (query Tardis API
   directly for available date ranges), or whether the backfill VM/launcher stopped/was de-prioritized.
2. **If Tardis has the data** → restore the UPBIT backfill (VM relaunch, fix whatever stopped it).
3. **If Tardis does NOT have the data** → operator decision needed: either (a) wire UPBIT live WS connectors to produce
   GCS objects (non-Tardis, on-demand capture going forward, with the pre-May-2026 Tardis data as historical floor), or
   (b) explicitly descope UPBIT from MVP with a documented ruling.

## Todos

- [x] ✅ [DATA] P1. **Diagnose the UPBIT May-2026 data gap root cause.** Root cause: pipeline-stoppage via code change —
      NOT a Tardis vendor ceiling. Two independent diagnoses (slot-6 + slot-15) converge on pipeline-stoppage: (1)
      **Primary/ongoing blocker (slot-6)**: `_filter_spot_only_venues` (introduced 2026-05-01 in deployment-service
      `3b635b9`) filters out spot-only venues when `_get_tardis_access_mode()` returns `perpetuals_only`. The
      `tardis-api-key-full` GCP secret **does not exist** — only `tardis-api-key` (perpetuals) exists — so
      auto-detection falls back to `perpetuals_only`, permanently excluding UPBIT from ALL new backfill VMs. (2)
      **Transition trigger (slot-15)**: A SPOT VM handling UPBIT was preempted ~May 22-24 (explaining the 2-day residual
      KRW-only book_snapshot_5 tail); pre-May-2026 preemption recovery wasn't wired for this launcher yet. Tardis API
      confirms UPBIT `"enabled": true` with trade+orderbook+ticker channels, symbols added as recently as 2026-07-31.
      Launcher config correctly includes UPBIT (`VENUES`, years 2022-2026, heavy group). **Verdict: code-level filter
      blocks all new VMs from scheduling UPBIT; the transition was a SPOT preemption of the last pre-filter VM.** —
      deployment-service@`3b635b9`, market-tick-data-service@N/A
- [ ] [DATA] P1. Restore UPBIT backfill: confirm/set `TARDIS_ACCESS_MODE=full_access` (or point config's
      `secrets.full_access` at the already-verified `tardis-api-key`), check the live VM fleet for the Tardis
      1-concurrent-VM cap, then relaunch `VENUES="UPBIT" YEARS="2022 2023 2024 2025 2026" LAUNCH_GROUPS="heavy" bash
      launch-cefi-sharded-backfill.sh` and verify ≥3 consecutive recent days of UPBIT trade+book_snapshot_5 objects in
      GCS (historical shape ~600-608 objects/day). Self-justified, no operator gate needed — standard idempotent
      MVP-venue backfill launch via the existing, already-used script (`FORCE=false` semantics skip already-captured
      dates; additive capture, not a delete).
      **2026-08-16 na-eligibility-audit correction**: the prior credential-gap framing on this item (2026-08-06 reopen)
      is FALSIFIED by direct measurement — `tardis-api-key-full` is still not found in Secret Manager, but the
      existing `tardis-api-key` secret already carries full UPBIT/spot entitlement (live Tardis datasets API returned
      HTTP 302 — authorized — for UPBIT KRW-BTC on 2026-05-20/07-20/08-10 and book_snapshot_5 on 2026-07-20; a sibling
      doc, `cefi_hl_aster_batch_data_gaps_2026_06_22.md`, independently established the same secret is
      `dataPlan:unlimited` and that the now-missing `-full`/`-backup` duplicates were BYTE-IDENTICAL deletions, not a
      real capability gap). MTDS's actual fetch client (`TardisBaseClient`) already uses `tardis-api-key`
      unconditionally with no spot-venue gate — only deployment-service's shard-scheduling filter
      (`_get_tardis_access_mode()`) checks the (irrelevant) `tardis-api-key-full` secret NAME. No new vendor
      credential is needed; this is worker-determinable config + relaunch + verify.
      **Separate data-pipeline-correctness flag for the operator** (found during this same measurement, not yet
      Progress-Log'd anywhere): live GCS shows an UNDOCUMENTED partial catch-up already happened and then silently
      re-stalled — real UPBIT trade+book_snapshot_5 objects exist for 2026-05-25 (608), 2026-05-26 (601), and
      2026-06-01 (613), written 2026-08-06T12:07Z→2026-08-07T02:05Z (almost certainly via the `TARDIS_ACCESS_MODE`
      override named above, since the `-full` secret was still absent at write time) — then ZERO UPBIT objects again
      for every date spot-checked 2026-06-15 through 2026-08-15 (12 dates), with no `cefi-upbit-*` VM (running or
      terminated) in the current fleet and no Progress Log entry documenting either the catch-up or the re-stall. The
      relaunch above should also confirm whether this run needs to resume from 2026-06-02 (not 2026-05-25) given the
      partial catch-up, and the silent-stall mechanism (why the catch-up VM stopped with no alert/record) is worth its
      own look independent of this todo.

## Progress Log

_Initial finding filed 2026-08-04 by slot-6 (data_engineering) as part of
`cefi_consolidated_native_ao_extract_2026_07_25.md` Todo 6._

### Root-cause diagnosis — 2026-08-04 by slot-15 (data_engineering)

**Verdict: PIPELINE STOPPAGE** (not Tardis vendor ceiling, not launcher config exclusion).

**Evidence:**

1. **Tardis API (a) — data IS available past 2026-05-22**: Direct `GET /v1/exchanges/upbit` query to `api.tardis.dev`
   confirms UPBIT is `"enabled": true`, available since `2021-03-03`, with **no exchange-level `availableTo`**. Symbols
   have been added as recently as **2026-07-31** (4 days before this diagnosis) — e.g. `BTC-AI` added 2026-06-30,
   multiple symbols added 2026-07-28 through 2026-07-31. This conclusively rules out "Tardis stopped carrying UPBIT
   data."

2. **Launcher config (c) — UPBIT IS included and NOT disabled**: `launch-cefi-sharded-backfill.sh` line 636 includes
   `UPBIT` in the default `VENUES` list alongside all other CEFI spot venues. The `_venue_years()` function (line 652)
   assigns UPBIT years `2022 2023 2024 2025 2026`. UPBIT is correctly classified as spot-only (`_venue_is_derivatives`
   returns 1 for UPBIT — it only gets the "heavy" group with `trades;book_snapshot_5`, no light/derivatives group). No
   config exclusion, no commented-out UPBIT, no de-prioritization.

3. **VM logs (b) — pattern matches SPOT preemption without auto-recovery**: The degradation pattern (2026-05-22: 606
   objects → May 23-24: 36 book_snapshot_5-only, KRW pairs only, no trades → May 25+: zero) is characteristic of a SPOT
   VM that was preempted mid-backfill and never auto-recovered. The `cefi-coverage-backfill` VM task uses SPOT by
   default (`--provisioning-model=SPOT`), and pre-May-2026 the preemption recovery infrastructure (`RelaunchPreemptedVm`
   actuator) may not have been in place for this launcher (the `lc_write_launch_params` +
   `lc_write_preemption_signal_file` preemption-recovery wiring was added 2026-07-15 per
   `cefi_completion_program_2026_07_15.md`). The 2-day residual tail (May 23-24 with KRW-only book data) is consistent
   with a partially-completed shard that finished its in-flight work before the VM terminated.

### Root-cause addendum — 2026-08-04 by slot-6 (data_engineering)

**Why new VMs can't resume UPBIT — the ongoing blocker beyond the preemption:**

4. **Shard-distribution filter (slot-6)**: The `_filter_spot_only_venues` method in
   `deployment_service/calculators/shard_distribution.py` (introduced 2026-05-01, commit `3b635b9`) removes UPBIT from
   ALL shard combinations when `_get_tardis_access_mode()` returns `perpetuals_only`. That method checks for the
   `tardis-api-key-full` GCP secret — **which does NOT exist** (confirmed:
   `gcloud secrets versions access latest --secret=tardis-api-key-full` → `NOT_FOUND`). Only `tardis-api-key`
   (perpetuals) exists. So every new VM launch since the code deploy sees `perpetuals_only` mode → UPBIT filtered out →
   zero shards scheduled → zero data. This is the ONGOING blocker; the SPOT preemption (finding 3) was the transition
   trigger that surfaced it.

**Synthesis**: The pre-May-2026 VMs were launched before the `_filter_spot_only_venues` code was deployed, so they
processed UPBIT normally. When the last UPBIT-capable VM was preempted ~May 22-24, all subsequent VMs launched with the
new code, hit the secret-missing → perpetuals_only → filter path, and never scheduled UPBIT. Both findings are correct
and complementary: slot-15 identified the transition trigger (SPOT preemption), slot-6 identified the ongoing blocker
(missing secret → spot-only filter).

**Recommendation for Todo 2**: Since Tardis carries the data and the launcher config is correct, **create the
`tardis-api-key-full` secret** (or set `TARDIS_ACCESS_MODE=full_access` override), then relaunch:
`VENUES="UPBIT" YEARS="2022 2023 2024 2025 2026" LAUNCH_GROUPS="heavy" bash launch-cefi-sharded-backfill.sh`.
**[OPERATOR] action**: obtain Tardis full-access API key and create the secret.

- **context-scout 2026-08-06**: populated context_scope (4 entries).

- **2026-08-11 (slot 1): `assigned_vm` corrected `planning` → `NA`.** Every remaining open todo here is operator-gated
  (BLOCKED-CREDENTIALS — operator-gated on a Tardis full-access key), so AO can see nothing to dispatch — the doc was an
  `assigned_vm: planning` plan the orchestrator never touches, which is exactly the condition
  `check_ao_dispatch_visibility_gate.py`'s `max_zero_dispatchable_docs` axis exists to flag. `NA` is the semantically
  correct value per `assigned_vm` (`planning` = the orchestrator VM executes it; `NA` = not dispatched). NO todo text,
  marker, or priority was altered — the exclusion markers were re-read and are correct and deliberate, not stale. Flip
  back to `planning` if and when the gate opens and the work becomes worker-determinable.

### Config fix shipped — 2026-08-17 by slot-3 (data_engineering)

**Shipped the worker-determinable part of Todo 2**: `configs/data-providers.yaml`'s `tardis.mode` was `auto`, and the
auto-detect path (`CombinationCalculator._get_tardis_access_mode`, `deployment-service/deployment_service/calculators/
shard_distribution.py`) probes for a DISTINCT `tardis-api-key-full` secret that has never existed in Secret Manager —
so auto-detect was permanently resolving `perpetuals_only` and silently excluding every `spot_only_venues` entry
(BINANCE-SPOT, COINBASE, UPBIT) from every new CeFi backfill VM scheduled through `shard_calculator.py`. Per the
2026-08-16 na-eligibility-audit correction above (measurement already confirmed `tardis-api-key` carries full
entitlement), pinned `mode: full_access` directly instead of relying on the never-created secret. Shipped:
`unified-trading-pm@5223b9c7b9` (`configs/data-providers.yaml`).

**Relaunch blocked by the Tardis 1-concurrent-VM cap, not by anything worker-determinable left undone.** Checked the
live fleet before attempting the relaunch (`gcloud compute instances list --filter="name~'^(cefi|tradfi)-.*-(heavy|
light)-'"`): `cefi-binance-futures-2026-heavy-*` is RUNNING and actively fetching real data (`run.log` showing live
`StreamingParquetWriter: uploaded` lines for day=2026-03-03 of a full 2022-2026 BINANCE-FUTURES heavy shard as of this
check) — this occupies the hard `TARDIS_MAX_CONCURRENT_VMS=1` cap (`tardis-concurrency-guard.sh`), so
`VENUES="UPBIT" YEARS="2022 2023 2024 2025 2026" LAUNCH_GROUPS="heavy" bash launch-cefi-sharded-backfill.sh` would be
refused (fail-closed by design) if run right now. At ~2 months of a ~7.5-month year processed in ~7.5h of wall-clock,
this shard is genuinely still hours from done, not stuck. Not forcing past the cap (`FORCE=1` is operator-only, and
N>1 Tardis VMs is a confirmed mutual-403 storm per `vm-launcher-runbook.md`). Relaunch + the ≥3-consecutive-day GCS
verification remain open — pick up once the fleet check shows the Tardis slot free
(`gcloud compute instances list --filter="name~'^(cefi|tradfi)-.*-(heavy|light)-'"` returns nothing RUNNING), then run
the relaunch command above and verify per the todo.

### Re-checked, cap still occupied — 2026-08-17 (slot-21, data_engineering)

Re-dispatched onto this same todo. Fleet check (`gcloud compute instances list --filter="name~'^(cefi|tradfi)-.*-
(heavy|light)-'"`) shows the **identical** VM slot-3 found — `cefi-binance-futures-2026-heavy-20260817-010713` — still
`RUNNING` (same name, same zone `asia-northeast1-c`), so the Tardis 1-concurrent-VM cap is unchanged and the relaunch
is still fail-closed-refused if attempted. Not re-verifying `run.log` progress independently (slot-3's check was hours
ago, same session day, and a preempted VM would read `TERMINATED` here, not `RUNNING` — no need to spend an SSH round
trip re-confirming liveness slot-3 already established). Not forcing past the cap. Releasing again with
`reason_code: GATED` rather than busy-polling a multi-hour VM from an interactive slot — resume condition unchanged:
the fleet check above returning nothing `RUNNING` for the cefi/tradfi heavy/light pattern.

### Re-checked again, cap still occupied — 2026-08-17 (slot-6, data_engineering)

Re-dispatched onto this same todo (resumed session). Fleet check (`gcloud compute instances list
--filter="name~'^(cefi|tradfi)-.*-(heavy|light)-'"`) shows the same VM `cefi-binance-futures-2026-heavy-20260817-010713`
still `RUNNING`, same zone. No change since slot-21's check. Not forcing past the Tardis 1-concurrent-VM cap. Releasing
again with `reason_code: GATED` — resume condition unchanged: the fleet check above returning nothing `RUNNING` for the
cefi/tradfi heavy/light pattern.

- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).
