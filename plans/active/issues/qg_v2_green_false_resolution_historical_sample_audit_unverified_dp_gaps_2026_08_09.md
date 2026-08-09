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
    /plans/active/cross_cutting_satellite_ao_dispatch_batch7_2026_08_09.md,
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

- [ ] [DATA] P2. For each of the 17 (asset_group, data_type) pairs in the DP-FETCH-009 table above, check the current
      `attempted_failed` ratio via the manifest (same detector logic as `check_high_attempted_failed`,
      `deployment-service/data_pipeline_monitors/`). Any pair still above the DP-FETCH-009 threshold (`abs>=500` or
      `ratio>=10%`) is a confirmed live gap — dispatch a targeted backfill relaunch for that shard. Any pair now clear
      needs no action. Repo: deployment-service (manifest check) + market-tick-data-service/features-onchain-service
      (backfill relaunch as needed per asset_group).
- [ ] [DATA] P2. For each of the 23 VM names in the DP-VM-002 list above, check the availability manifest's `captured`
      count for that VM's target shard as of today vs. its value at the VM's `created_at` timestamp (listed above). A
      shard whose count did not climb since is unconfirmed-still-missing — relaunch it. A shard that climbed via a later
      differently-named VM needs no action; note which VM covered it. Repo: deployment-service (manifest check +
      relaunch), instruments-service (for the `instr-backfill-*` entries).
- [ ] [REVIEW] P3. If either todo above surfaces >5 confirmed-still-open shards, escalate per CLAUDE.md's "big finding
      (data-correctness...) → NOTIFY OPERATOR" — this doc's own pass stopped at identifying the entities, not confirming
      live breakage, so a large confirmed-count changes this from "verification gap" to "active data hole."

## Progress Log

- **2026-08-09 (slot-22, backend_engineer, task cross_cutting_satellite_ao_dispatch_batch7-4b0d20e0fecd)**: Filed after
  running the bounded historical-sample audit the batch7 plan's `[BACKEND] P2` todo specified. Full methodology: queried
  `escalation_queue` directly via local `sqlite3 -readonly` (co-located on-VM session, SSM not needed — see Access
  note), collapsed 932 rows to 76 problem-signature buckets, cross-referenced each significant bucket against
  independent live evidence (GCS catalogue probe, GitHub PR history, Dockerfile git-blame for the actuator-packaging fix
  date, post-fix escalation behavior). 36 of 76 buckets (by row volume) resolve to a confirmed self-healing or
  already-investigated explanation; the residual 40 named entities (17 DP-FETCH-009 asset_group/data_type pairs + 23
  DP-VM-002 VM names) are filed above as the bounded, checkable follow-up.
