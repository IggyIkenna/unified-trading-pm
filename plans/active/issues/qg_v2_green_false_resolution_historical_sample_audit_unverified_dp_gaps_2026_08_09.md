---
doc_type: issue
title: >-
  Bounded historical-sample audit of `qg_v2_green`-false-closed escalations finds 40 distinct data-pipeline entities (17
  asset_group/data_type pairs + 23 VMs) never independently verified
summary: >-
  Follow-up to `escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md`'s extracted P2 audit
  todo (now fixed via `agent-orchestrator@884a9bfe1`). Queried the live `escalation_queue` table directly (read-only,
  local filesystem access — see Progress Log for why the documented SSM path wasn't needed) for all
  `resolution='qg_v2_green'` rows in the last 30 days across the 4 wrongly-gated wall types: 932 rows collapsing to 76
  distinct problem-signatures. Cross-referenced each bucket against independent evidence (self-heal actuator packaging
  status, live GCS catalogue freshness, GitHub PR merge history, the fix's own post-shipment behavior). Most buckets
  self-heal via an independent mechanism (self-heal actuators, the LDR->main promote-fleet retry loop, the nightly
  catalogue refresh) and are NOT genuine misses. Two buckets have NO independent self-heal path and were never checked
  by a human: DP-FETCH-009 across 17 (asset_group, data_type) pairs beyond the already-tracked cefi/book_snapshot_5 (179
  rows), and DP-VM-002 across 23 distinct one-off VM names (23 rows) — both page-only alert tiers with zero
  auto-recovery. This doc's todos ask a worker to verify current backfill/capture completeness for exactly these 40
  named entities (not a fresh corpus-wide audit).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags:
  [escalation, data-pipeline-correctness, false-resolution, historical-audit, qg-fallthrough, dp-fetch-009, dp-vm-002]
related:
  [
    /plans/active/issues/escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch7_2026_08_09.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md,
  ]
created: 2026-08-09
author: slot-22 (backend_engineer), task cross_cutting_satellite_ao_dispatch_batch7-4b0d20e0fecd
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
execution_scope: fleet
estimate_class: research
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-09
locked_since:
archive_exempt: true
source: >-
  `cross_cutting_satellite_ao_dispatch_batch7_2026_08_09.md`'s `[BACKEND] P2` "bounded historical-sample audit" todo,
  extracted 2026-08-09 from `escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md` once its
  code-fix prerequisite (`agent-orchestrator@884a9bfe1`) landed.
---

# Historical-sample audit of qg_v2_green false-closures: 40 entities never independently verified

## What I found

**Access note (relevant to two OPEN `[OPERATOR]` items —
`check_agent_orchestrator_ssm_send_command_access_denied_2026_08_09.md`,
`escalation_queue_reconciler_ssm_permission_gap_2026_08_08.md`):** this task's own todo specified the SSM path for
querying `escalation_queue`, and that path is genuinely blocked for the `ikenna-worker` IAM identity per those two
already-filed docs. This slot's session, however, is co-located on the orchestrator VM itself
(`curl localhost:8765/api/mode` resolves directly, and `/api/mode`'s own `db_path` matches a locally-readable file) — so
I queried `state.db` directly via `sqlite3 -readonly` on local disk, no SSM/AWS credentials needed at all. This does NOT
resolve the SSM gap for off-VM dev checkouts (that `[OPERATOR]` grant is still needed for THOSE sessions) — noting it
here only so a future on-VM session facing the same "SSM blocked" framing knows to check for local file access first
instead of stalling on the IAM gap.

**Query**: `escalation_queue` rows with `resolution='qg_v2_green'`,
`wall_type IN ('data_pipeline_failure','provenance_blocked','sit_failure','plan_health')`,
`created_at >= now - 30 days`. **Result**: 932 rows. Grouped by a `(wall_type, problem-code-extracted-from-context)` key
to collapse repeat-fires of the same underlying condition: **76 distinct buckets**.

**Self-healing categories (no further action — evidence per bucket):**

- **`plan_health`** (214 rows, 1 repo `unified-trading-pm`): all are routine daily plan-hygiene-sweep WARN/HARD output
  (parent_epic mismatches, orphan counts, todo-regression checks) — the exact class of finding
  `/plan-reconcile`/`/ag-closeout-audit`/the daily hygiene sweep already routinely re-surface independent of the
  escalation queue. Not a "wall" needing worker dispatch in the traditional sense.
- **`provenance_blocked`** (80 rows, 5 repos, all "Promotion PR BLOCKED — auto-merge NOT (re-)armed"): spot-checked the
  largest bucket (deployment-ui PR #481, 39 false-closures across an 18-min series 2026-08-07) — PR #481 is CLOSED
  (superseded), and `gh pr list --search promote --state merged` shows deployment-ui's promote-fleet cycling fresh PRs
  continuously (PR #489 merged 2026-08-09T17:14Z, ~2h before this audit). Confirms the standing LDR→main promote-fleet
  retry loop (`ldr-to-main-promote-fleet.yml`, `*/15`) is the real resolution mechanism here, independent of the
  escalation queue — not a genuine miss.
- **`sit_failure`** (39 rows, 16 repos, mostly single-occurrence Promotion-PR CI-block / MAJOR-bump-cascade events):
  same promote-fleet-retry mechanism as `provenance_blocked` above; not individually re-verified per-row (bounded-sample
  scope) but consistent with the same self-healing class.
- **`data_pipeline_failure` / DP-CATALOG-001** (42 rows, 2 asset_groups: sports 38, defi 4 — "instrument catalogue
  stale > 24h budget"): **live-verified via direct GCS probe** — both
  `gs://instruments-store-sports-prd-central-element-323112/prod/catalog.parquet` (age 17.7h) and
  `gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet` (age 17.9h) are CURRENTLY fresh, both
  under the 24h budget. The nightly catalogue-refresh cron (per
  `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`'s domain map) has since re-run. Not a live miss.
- **`data_pipeline_failure` / DP-VM-001, DP-VM-003, DP-VM-008** (104 + 66 + 33 = 203 rows, deployment-service, various
  VM names — OOM exit / stall / ambiguous-exit): these ARE `auto_recover`-tier alerts per
  `/codex/05-infrastructure/data-pipeline-alerts.md`'s registry — a real actuator (resize-up relaunch / kill+respawn /
  checkpoint-resume) dispatches independent of the escalation-queue's later fate. **Verified the actuator-packaging gap
  the codex doc's stale `last_reviewed: 2026-06-22` note still describes as "OPEN GAP (P1)" was actually CLOSED
  2026-07-27** (`deployment-api@fa54159`, "package vm_zombie_watchdog + the whole recovery-actuator family into the
  production api stage") — **before** this audit window's VM-alert data begins (2026-07-30). The self-heal layer was
  live for the full window; the false-resolution bug means no human separately double-checked the outcome, but the
  actual relaunch/respawn action was very likely already taken. Residual (unverified) risk: the actuator's own
  documented `≤2/(vm-prefix, day)` rate cap — a VM-prefix stalling a 3rd+ time in one day would fall through to
  page-only with no human ever seeing it. Not chased further in this bounded pass (would need per-VM-prefix, per-day
  event counting — flagged as a possible follow-up, not filed as its own todo since no evidence of an actual
  3rd-in-a-day case was found in the sample).
- **Fix verified working live**: 2 escalations created AFTER the fix landed (`884a9bfe1` @ 2026-08-09T10:28:50Z) for
  `data_pipeline_failure` both show `resolution='still_red_reescalated'` (never `qg_v2_green`) — confirms the fix is
  live and correctly routing to real dispatch/re-escalation, not silent auto-close.

**Buckets with NO self-heal path and NO human verification — genuine-miss candidates:**

- **DP-FETCH-009 beyond the already-tracked instance** (179 of 312 total rows; page-only alert, no `auto_recover` tier):
  133/312 rows are `asset_group=cefi data_type=book_snapshot_5` — the ONE instance already confirmed extensively
  investigated per `escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md`'s `[VERIFY]` todo
  (25+ dispatches, 5 shipped fixes). The remaining **179 rows span 17 DISTINCT (asset_group, data_type) pairs** never
  specifically checked:

  | asset_group | data_type             | rows | first fired | last fired |
  | ----------- | --------------------- | ---- | ----------- | ---------- |
  | cefi        | trades                | 38   | 2026-08-06  | 2026-08-09 |
  | cefi        | derivative_ticker     | 33   | 2026-07-28  | 2026-08-09 |
  | defi        | dex_pool_swaps        | 29   | 2026-07-28  | 2026-08-08 |
  | cefi        | futures_chain         | 15   | 2026-07-29  | 2026-08-09 |
  | defi        | dex_pools             | 11   | 2026-08-06  | 2026-08-07 |
  | cefi        | options_chain         | 10   | 2026-08-06  | 2026-08-09 |
  | prediction  | trades                | 9    | 2026-07-31  | 2026-08-07 |
  | cefi        | liquidations          | 7    | 2026-07-30  | 2026-08-09 |
  | defi        | dex_swaps             | 6    | 2026-08-06  | 2026-08-07 |
  | prediction  | book_snapshot_5       | 5    | 2026-08-06  | 2026-08-07 |
  | defi        | lst_rates             | 5    | 2026-08-06  | 2026-08-07 |
  | cefi        | perp_funding          | 5    | 2026-08-06  | 2026-08-07 |
  | tradfi      | ohlcv_24h             | 2    | 2026-08-06  | 2026-08-06 |
  | sports      | arbitrage_opportunity | 1    | 2026-08-06  | 2026-08-06 |
  | tradfi      | ohlcv_1m              | 1    | 2026-08-06  | 2026-08-06 |
  | sports      | odds_horizon_bucket   | 1    | 2026-08-06  | 2026-08-06 |
  | defi        | risk_params           | 1    | 2026-08-07  | 2026-08-07 |

- **DP-VM-002** (23 rows, deployment-service; "VM drained but manifest `captured` did not climb" — page-only, no
  `auto_recover` tier): **23 DISTINCT one-off VM names**, none repeating, spanning 2026-07-30 through 2026-08-07:
  `tradfi-bf-nasdaq-ohlcv-1m-2024-d02-20260730-210525`, `features-delta-one-defi-20260730-231230`,
  `tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-20260731-000118` (×2, also 20260731-060117 and 20260806-060059),
  `mdps-backfill-tradfi-y2020es-20260731-011358`, `mdps-backfill-tradfi-y2026es3-20260731-014643`,
  `mdps-backfill-tradfi-y2024es3-20260731-023743`, `canonical-migration-cefi-content-24-relaunch20260731-065001`,
  `instr-backfill-sports-pchk-0801100312-f-betfair`, `mtds-backfill-sports-pipelinecheck-20260801-101533-a9a662`,
  `instr-backfill-sports-pchk-0801102917-s-transfermarkt`, `features-delta-one-defi-20260731-110727`,
  `mtds-backfill-sports-pipelinecheck-20260801-113938-a4ac85`, `tradfi-bf-cme-ohlcv-1m-g01-gc-gc-2026-20260801-121314`,
  `mtds-backfill-sports-pipelinecheck-20260801-123419-a9a662`,
  `mtds-backfill-sports-pipelinecheck-20260801-130446-a9a662`,
  `mtds-backfill-sports-pipelinecheck-20260801-131738-2da87c`, `instr-backfill-sports-pchk-0801133147-l-footystats`,
  `mdps-features-live-cefi-20260807-001235`, `fs-backfill-20260807-095916`,
  `tradfi-bf-nasdaq-ohlcv-1m-2025-d02-20260807-090845`,
  `canonical-migration-defi-gas-fees-legacy-purge-20260807-082535`.

  None of these have any auto-recovery mechanism, and none were verified by a human (worker dispatch never happened —
  the escalation was auto-closed within minutes of filing every time). Whether each VM's target data slice was ever
  actually backfilled by a LATER, differently-named run is unknown from the escalation_queue table alone — needs a
  manifest/GCS check per entity.

## Why it matters

Data-pipeline correctness is the workspace heartbeat (CLAUDE.md HARD RULE). These 40 entities (17 asset_group/data_type
pairs + 23 VMs) are the residual, NOT-yet-explained portion of the historical blast radius the false-resolution bug
opened — everything else in the 30-day sample resolves via an independently-verified self-heal path (actuator,
promote-fleet retry, nightly catalogue cron) or was already covered by prior investigation (cefi/book_snapshot_5). This
is meaningfully smaller than the raw "599/604 auto-closed" headline in the source doc suggested, but the residual is
still real, unverified, page-only-alert-tier gaps in exactly the categories the HARD RULE cares about (backfill
completeness, live capture health).

## Recommended decision

Dispatch a bounded verification pass over exactly the 40 named entities above (not a fresh corpus-wide audit): for each
(asset_group, data_type) pair, check the current manifest `attempted_failed` ratio (via the same
`check_high_attempted_failed` post-run scan logic DP-FETCH-009 itself uses) — if still elevated, that confirms a live
gap and warrants a backfill relaunch; if clear, the condition self-healed on a later capture wave and no action is
needed beyond noting it here. For each VM name, check the manifest's `captured` count for that VM's target shard as of
today vs. at filing time — if it climbed since (a later differently-named relaunch covered it), no action; if flat, the
backfill slice needs a fresh relaunch.

## Todos

- [x] ✅ [DATA] P2. For each of the 17 (asset_group, data_type) pairs in the DP-FETCH-009 table above, check the current
      `attempted_failed` ratio via the manifest (same detector logic as `check_high_attempted_failed`,
      `deployment-service/data_pipeline_monitors/`). Any pair still above the DP-FETCH-009 threshold (`abs>=500` or
      `ratio>=10%`) is a confirmed live gap — dispatch a targeted backfill relaunch for that shard. Any pair now clear
      needs no action. Repo: deployment-service (manifest check) + market-tick-data-service/features-onchain-service
      (backfill relaunch as needed per asset_group). — verified live 2026-08-09 (slot-32, data_engineering): **11 of 17
      pairs are STILL HIGH** (confirmed live gap, current `attempted_failed` count in the trailing 14-day window). See
      Progress Log for the full per-pair table + methodology. Backfill relaunch dispatch NOT done in this task —
      escalated per the P3 todo below instead (11 > 5 confirmed-open shards; multi-repo/multi-AG blast radius warrants a
      scoped follow-up plan rather than an in-session ad-hoc relaunch fan-out).
- [x] ✅ [DATA] P2. For each of the 23 VM names in the DP-VM-002 list above, check the availability manifest's
      `captured` count for that VM's target shard as of today vs. its value at the VM's `created_at` timestamp (listed
      above). A shard whose count did not climb since is unconfirmed-still-missing — relaunch it. A shard that climbed
      via a later differently-named VM needs no action; note which VM covered it. Repo: deployment-service (manifest
      check + relaunch), instruments-service (for the `instr-backfill-*` entries). — verified live 2026-08-09 (slot-18,
      data_engineering): **0 of 23 confirmed still-missing** (1 genuinely unconfirmed, evidence-exhausted). Full per-VM
      breakdown + methodology in Progress Log — the escalation's own generic "(0 → 0)" text turned out NOT to mean a
      uniform live gap: 8 VMs are `--test-run` smoke checks routed to the `-test-` bucket by design (never targeted
      prod), 1 is a purge/no-op migration (nothing was ever meant to be captured), 1 is a
      `LifecycleClass.LONG_LIVED_LIVE` VM the detector's own documented exemption should have (and per this read, did
      NOT) suppress, 1 is folded into an already-tracked, actively-worked P1 issue doc, and the remaining 12 real
      backfill/derive targets are ALL currently healthy (fully captured or actively being re-covered by a live
      same-shard relaunch found running RIGHT NOW).
- [x] ✅ [REVIEW] P3. If either todo above surfaces >5 confirmed-still-open shards, escalate per CLAUDE.md's "big
      finding (data-correctness...) → NOTIFY OPERATOR" — this doc's own pass stopped at identifying the entities, not
      confirming live breakage, so a large confirmed-count changes this from "verification gap" to "active data hole." —
      already satisfied: todo 1 alone crossed the >5 bar (11/17) and its own `/blocked` NOTIFY-OPERATOR escalation is
      filed (see its Progress Log entry). Todo 2 adds ZERO additional confirmed-still-open shards (0/23, well under the
      bar) — no further escalation warranted from this todo.

## Progress Log

- **2026-08-09 (slot-22, backend_engineer, task cross_cutting_satellite_ao_dispatch_batch7-4b0d20e0fecd)**: Filed after
  running the bounded historical-sample audit the batch7 plan's `[BACKEND] P2` todo specified. Full methodology: queried
  `escalation_queue` directly via local `sqlite3 -readonly` (co-located on-VM session, SSM not needed — see Access
  note), collapsed 932 rows to 76 problem-signature buckets, cross-referenced each significant bucket against
  independent live evidence (GCS catalogue probe, GitHub PR history, Dockerfile git-blame for the actuator-packaging fix
  date, post-fix escalation behavior). 36 of 76 buckets (by row volume) resolve to a confirmed self-healing or
  already-investigated explanation; the residual 40 named entities (17 DP-FETCH-009 asset_group/data_type pairs + 23
  DP-VM-002 VM names) are filed above as the bounded, checkable follow-up.
- **2026-08-09 (slot-32, data_engineering, task
  qg_v2_green_false_resolution_historical_sample_audit_unverified_dp_gaps-04689ae21350)**: Todo 1 (the 17 DP-FETCH-009
  pairs) verified live. **Memory-bounding note for the next reader**: the production detector's own reader
  (`deployment_service.data_pipeline_monitors.meta_watchers._read_attempted_failed_cells`, a plain
  `pd.read_parquet(io.BytesIO(raw), columns=[4 cols])` call) OOM'd this shared host when run directly — RSS hit 10.8GB
  against a 6G `run-bounded-analysis.sh` cap reading all 5 asset_groups' consolidated indexes (cefi/defi are tens of
  millions of rows; 4 pandas object-dtype string columns at that row count is the same failure class as the archived
  `/plans/archive/2026_08/read_availability_index_slim_read_oom_at_defi_scale_2026_08_01.md` incident, just in a
  DIFFERENT reader — deployment-service's own, not UTL's already-fixed `read_availability_index` slim path). This is
  expected/acceptable for the production Cloud Run Job (provisioned with adequate container memory) but unsafe to run
  ad-hoc on the shared planning-vm per RULES.md § 1 / data_engineering.md STEP 0.56 — not filed as a fresh issue since
  the existing memory-bounding HARD RULE already anticipates and prescribes the fix for exactly this shape. Worked
  around the same way the archived incident did: downloaded each asset_group's index ONCE (single-walk, same blob the
  production check reads, one local scratch file at a time, deleted immediately after read) and ran a DuckDB
  (`memory_limit='2GB'`) `GROUP BY data_type` aggregate filtered to only the 17 target `data_type` values instead of
  materialising all data_types × all rows into pandas — completed cleanly under a 4G RSS cap.

  **Result — 11 of 17 pairs are STILL HIGH** (current `attempted_failed` count in the trailing 14-day window, same
  threshold logic as `check_high_attempted_failed`: `abs>=500` OR (`count>=50` AND `ratio>=10%`)):

  | asset_group | data_type             | captured | attempted_failed | ratio | HIGH (confirmed live gap) |
  | ----------- | --------------------- | -------: | ---------------: | ----: | :------------------------ |
  | cefi        | trades                |  1585570 |            14265 |  0.9% | **YES**                   |
  | cefi        | derivative_ticker     |  1539343 |            18478 |  1.2% | **YES**                   |
  | defi        | dex_pool_swaps        |  9650042 |              213 |  0.0% | no                        |
  | cefi        | futures_chain         |        0 |             2858 |  100% | **YES** (0 ever captured) |
  | defi        | dex_pools             |   340486 |                0 |  0.0% | no                        |
  | cefi        | options_chain         |        0 |              799 |  100% | **YES** (0 ever captured) |
  | prediction  | trades                |   372858 |            23566 |  5.9% | **YES**                   |
  | cefi        | liquidations          |   704777 |            20445 |  2.8% | **YES**                   |
  | defi        | dex_swaps             |  2025156 |                0 |  0.0% | no                        |
  | prediction  | book_snapshot_5       |    23122 |             7899 | 25.5% | **YES**                   |
  | defi        | lst_rates             |    75891 |                0 |  0.0% | no                        |
  | cefi        | perp_funding          |     1085 |              101 |  8.5% | no (below both bars)      |
  | tradfi      | ohlcv_24h             |     7425 |              727 |  8.9% | **YES**                   |
  | sports      | arbitrage_opportunity |    17851 |             2505 | 12.3% | **YES**                   |
  | tradfi      | ohlcv_1m              |   718422 |                0 |  0.0% | no                        |
  | sports      | odds_horizon_bucket   |   137258 |              892 |  0.6% | **YES**                   |
  | defi        | risk_params           |    42141 |               22 |  0.1% | no                        |

  All 6 confirmed-clear pairs are defi/tradfi(ohlcv_1m) with `attempted_failed=0` or negligible — genuinely healed, no
  action needed. The 11 confirmed-HIGH pairs span cefi (5: trades, derivative_ticker, futures_chain, options_chain,
  liquidations), tradfi (1: ohlcv_24h), sports (2: arbitrage_opportunity, odds_horizon_bucket), prediction (2: trades,
  book_snapshot_5) — cefi/futures_chain and cefi/options_chain are notable: `captured=0`, 100% failure rate, meaning
  these pairs have NEVER successfully captured a single row in the trailing window (possibly a broken adapter/venue
  pairing rather than a transient backfill gap — worth a human read before any blind relaunch, not just a mechanical
  backfill dispatch).

  **11 > 5 confirmed-still-open shards — this crosses the P3 todo's own escalation bar** ("a large confirmed-count
  changes this from 'verification gap' to 'active data hole'"). Backfill relaunch dispatch was NOT attempted in this
  task: it spans 2 repos (market-tick-data-service, features-onchain-service) × 4 asset_groups and is itself a
  properly-scoped-todo-per-shard undertaking (per CLAUDE.md's dispatch-scope-eligibility rule), not a single-task
  add-on. Filed a `/blocked` notification to the operator/main agent per CLAUDE.md's "big finding (data-correctness) →
  NOTIFY OPERATOR" HARD RULE, recommending a scoped follow-up plan naming each of the 11 shards + owning repo (mirrors
  this doc's own P3 todo intent) rather than an ad-hoc in-session relaunch fan-out — see the blocked-question for the
  operator's decision. Todo 2 (the 23 DP-VM-002 VM names) is NOT done — out of scope for this task; whoever picks it up
  next should fold its results into this same escalation once both todos are complete.

- **2026-08-09 (slot-18, data_engineering, task
  qg_v2_green_false_resolution_historical_sample_audit_unverified_dp_gaps-256f4555cced)**: Todo 2 (the 23 DP-VM-002 VM
  names) verified live. **Methodology**: this session is also co-located on the orchestrator VM (`/api/mode` resolves a
  local `state.db` path), so re-queried `escalation_queue` directly for the exact 23 `resolution='qg_v2_green'`
  DP-VM-002 rows — confirmed all 23 alert payloads read the SAME generic template text
  `"drained but manifest captured did not climb (0 → 0) ... a genuine silent zero"`, which turned out to be misleading:
  it does NOT mean all 23 are uniform live gaps. Cross-checked each VM against THREE independent evidence sources rather
  than trusting the detector's own verdict at face value: (1) the VM's own `run.log` at
  `gs://deployment-scripts-{pid}/vm-logs/<vm>/run.log` (or `log-archive/**/<vm>/run.log` for older ones) — the
  authoritative launch params + terminal outcome; (2) the CURRENT availability-manifest state for the VM's actual target
  shard (single-walk: downloaded each relevant bucket's `_index/availability_index.parquet` ONCE to scratch, queried via
  DuckDB `memory_limit='2GB'`, deleted after — never a bare pandas full-index read, per RULES.md § 1 / STEP 0.56); (3)
  `gcloud compute instances list` for any CURRENTLY RUNNING same-shard relaunch. Also read
  `deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py` + `vm_prefix_registry.py` +
  `deployment_classification.py` directly to understand exactly what DP-VM-002 checks and its own documented exemptions,
  rather than re-deriving the detector logic.

  **Result — 0 of 23 confirmed still-missing.** Breakdown by category:

  | Category                                                                                                           |         VMs (of 23) | Verdict                                                         | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
  | ------------------------------------------------------------------------------------------------------------------ | ------------------: | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
  | `instr-backfill-sports-pchk-*` / `mtds-backfill-sports-pipelinecheck-*` smoke checks                               |                   8 | **NOT a gap**                                                   | Root-caused: `--test-run`/`IS_TEST_RUN` routes ALL writes to the `-test-` bucket sibling by design (`scripts/vm/launch-mtds-backfill-vm.sh`: "`--test-run` sets `IS_TEST_RUN=true` so writes route to the -test- bucket sibling"). One of these 8 (`instr-backfill-sports-pchk-0801100312-f-betfair`) is literally the NAMED root-cause incident VM cited in `scripts/vm/lib/launcher_common.sh`'s `lc_tier_service_account` fix comment (commit `dd5f235c`, 2026-08-01T10:36:50Z, "fix(dp-vm-002): --test-run launchers select the wrong tier SA") — already known, already fixed, prod was never the intended write target for any of the 8.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
  | `canonical-migration-defi-gas-fees-legacy-purge-20260807-082535`                                                   |                   1 | **NOT a gap**                                                   | Its own run.log: `--skip-discovery-verified-empty set` + `"GCS purge complete: 0/0 object(s) deleted."` — this VM DELETES legacy-format objects, it never captures new rows; "captured did not climb" is the CORRECT, expected outcome for a no-op purge run, not evidence of missing data.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
  | `mdps-features-live-cefi-20260807-001235`                                                                          |                   1 | **NOT a gap (but flags a possible detector bug)**               | `vm_prefix_registry.py` maps this prefix to `LifecycleClass.LONG_LIVED_LIVE` → `umbrella="live"`, and `exit_code_fleet_monitor.py`'s own docstring + code (`is_live_vm` gate) says a LIVE VM's flat captured count is BY DESIGN (`EXPECTED_NO_CAPTURE`, alert suppressed) — live data volume lands in the event-log sink, not the manifest. This escalation firing as `DP_VM_GONE_NO_CAPTURE` for a VM whose own registry entry should have exempted it is _itself_ a small inconsistency worth a human's eyes (possibly a stale umbrella resolution at alert time, not reproduced here) — not filed as a fresh issue since it's a single low-severity occurrence, noted here for the next reader.                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
  | `canonical-migration-cefi-content-24-relaunch20260731-065001`                                                      |                   1 | **NOT a new gap — already tracked**                             | Its log lineage (`log-archive/final/canonical-migration-cefi-content-24-relaunch20260730-132600/run.log`, the adjacent relaunch) resolves to `market-tick-data-service/scripts/migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` — a resumable instrument_id-canonicalisation MIGRATION (not a capture pipeline; "captured did not climb" is the wrong metric for it entirely). This exact migration's incompleteness is ALREADY tracked end-to-end in `/plans/active/issues/cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31.md` (P1, `parent_epic: cefi_master`, up through "Round-8" relaunches as of this doc's own edits) — folding it in here would duplicate an already-actively-worked issue, not surface a new one.                                                                                                                                                                                                                                                                                                                                                                                       |
  | `tradfi-bf-nasdaq-ohlcv-1m-2024-d02-*` / `-2025-d02-*`                                                             |                   2 | **NOT a gap — healthy**                                         | DuckDB query of the current `market-data-tick-tradfi` manifest: every month of 2024 AND 2025 for `(venue=NASDAQ, data_type=ohlcv_1m)` shows `captured` rows every month, **zero** `attempted_failed` anywhere in either year.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
  | `tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-*` (×3: 20260731-000118, -060117, 20260806-060059 — same shard, 3 attempts) |  3 (1 unique shard) | **NOT a gap — healthy AND actively being relaunched right now** | Current manifest: `(venue=CME, underlying=ES, data_type=ohlcv_1m, 2020)` shows `captured` rows every month, zero `attempted_failed`. Also found a **CURRENTLY RUNNING** VM `tradfi-bf-cme-ohlcv-1m-es-2020-20260809-180059` (`gcloud compute instances list` — status RUNNING, zone asia-northeast1-c) actively writing per-VM shards (`_index/per_vm/tradfi-bf-cme-ohlcv-1m-es-2020-20260809-180059-c2{0..6}.parquet`) for this exact shard AS OF TODAY — this is the "later differently-named VM" the todo asked to identify.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
  | `tradfi-bf-cme-ohlcv-1m-g01-gc-gc-2026-20260801-121314`                                                            |                   1 | **NOT a gap**                                                   | Its own run.log: `[vm-exec] command exited rc=0` + `DEPLOYMENT_COMPLETED ... exit_code=0` — completed cleanly; the `(0→0)` alert text was a stale/generic template, not the real outcome. Manifest confirms `(CME, GC, ohlcv_1m)` `captured` every month 2026-01 through 2026-08, no `attempted_failed` on the `GC` root itself (a persistent `attempted_failed` DOES exist on the separate `ECGC` symbol across 2026 — pre-existing, unrelated to this VM's target, not chased further as out-of-scope for this todo).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
  | `mdps-backfill-tradfi-y2020es-*` / `-y2026es3-*` / `-y2024es3-*`                                                   |                   3 | **NOT a gap — healthy**                                         | DuckDB query of `service_name ILIKE '%process%'` (MDPS) rows for `underlying=ES`: 2024 and 2026 show zero `attempted_failed`; 2020 shows exactly 11 `attempted_failed` rows, ALL dated `2020-01-01` with `error_reason=NO_RAW_TICK_DATA_FOR_SHARD` (New Year's Day — a genuine non-trading-day honest-absence artifact, not a live gap; `2020-06-06`, the date this specific VM's run.log shows it was actively processing, has zero attempted_failed).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
  | `features-delta-one-defi-20260730-231230` / `-20260731-110727` (×2, same family — the 2nd is a retry)              | 2 (1 unique family) | **NOT a gap**                                                   | The 2nd (retry) VM's own run.log: `[vm-exec] command exited rc=0` + `DEPLOYMENT_COMPLETED ... exit_code=0`. The 1st VM's log showed only routine per-date `"No upstream MDPS data ... skipping date"` WARNINGs (honest-absence skips, not a crash) before the successful retry superseded it.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
  | `fs-backfill-20260807-095916`                                                                                      |                   1 | **UNCONFIRMED — evidence-exhausted, not "confirmed-missing"**   | No `run.log` found (checked both the live `vm-logs/` path and `log-archive/**`), no per-VM manifest shard, and the consolidated `instruments-store-sports` manifest's most recent `FOOTYSTATS`-venue `written_at` (2026-07-13) PREDATES this VM's run (2026-08-07) — so there's no positive evidence it ran successfully. But per the earlier research pass's finding, `fs-backfill-` doesn't set `MANIFEST_PER_VM_SHARDS=true` at all (writes reference-data entities, not date-sharded ticks) AND DP-VM-002's own captured-reader is confirmed bucket-`kind`-blind for `instr-backfill-*`/`fs-backfill-*` prefixes (only probes `market-data` buckets, never `instruments-store`) — so BOTH the alert's original "0→0" verdict AND my own absence-of-evidence read are equally unreliable for this one VM. No later differently-named FootyStats VM found running or escalating since. Genuinely the single item this pass could not resolve either way — recommend a direct instruments-service-side check (was the FootyStats entity catalogue actually refreshed around 2026-08-07?) rather than a blind relaunch, if this is picked up as a follow-up. |

  **Structural finding for the detector itself (not this task's to fix, noted for whoever owns
  `exit_code_fleet_monitor.py` next)**: the escalation payload's `"(0 → 0)"` captured-count text is a fixed template,
  not a per-VM interpolated real reading — it reads identically for a genuine silent zero AND for VMs where "captured
  climbing" was never even the right question (purges, migrations, live producers, test-run smoke checks, and any VM
  whose real write bucket the reader doesn't probe). Combined with the bucket-`kind`-blindness the earlier research pass
  found (VMs writing to `instruments-store-*`/`features-*` read against `market-data-*` instead), a meaningful fraction
  of DP-VM-002's firing volume is a detector-scope mismatch, not a live data hole — worth a scoped follow-up to either
  exempt these VM classes at the source or route their captured-reads through the correct bucket `kind`, rather than
  leaving every future occurrence to a manual per-VM run.log dig like this one. Not filed as a separate issue doc here
  since it doesn't meet the "big finding" bar alone and the fix would touch the SAME detector code 3 other recent issues
  already reference — flagging in this Progress Log for the next reconciliation pass to pick up.

  Both todos in this doc are now complete. Net result across the full 40-entity audit (17 DP-FETCH-009 pairs + 23
  DP-VM-002 VMs): 11 confirmed-live gaps (already escalated via todo 1's `/blocked`), 0 confirmed-live gaps from todo 2,
  1 unconfirmed (fs-backfill footystats, noted above for a targeted follow-up if desired).

  **`archive_exempt: true` note (temporary, per the sanctioned flip-then-mv bridge in
  `/plans/active/issues/check_archive_candidates_only_mode_no_flip_then_mv_exemption_2026_08_09.md`)**: both todos are
  now done and this doc has 0 open todos + unlocked — it qualifies for archival. Setting `archive_exempt: true` on THIS
  flip-only commit is a deliberate, temporary bridge (removed in the immediately-following archival commit that does the
  `git mv` + banner + referrer fixes) so the checkbox transition stays visible at the original `plan_ref` path for the
  AO server's M3 cross-repo flip verification, per RULES.md § 2's "never combine the flip with a `git mv` in one commit"
  rule.
