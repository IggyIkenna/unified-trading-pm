---
title: vm-zombie-watchdog relaunch (dry_run=false) reaped 9 live campaign backfill VMs
created: 2026-06-23
author: ikennaigboaka [slot·ikenna-worker]
source:
  - plans/active/data_completion_to_100_all_ag_2026_06_21.md (INFRA P0 "Restore the genuinely-down infra")
  - scripts/vm/launch-vm-zombie-watchdog.sh
  - scripts/vm/vm_zombie_watchdog.py
locked_by: live-defi-rollout
---

## What I found

While restoring the genuinely-down `vm-zombie-watchdog` (its census blob
`vm-census/watchdog-census.json` was absent → `DP_ZOMBIE_WATCHDOG_DOWN`, because the
running VM `vm-zombie-watchdog-20260528-212634` was on 2026-05-28 code with NO
census-write), I relaunched it with the launcher **default `dry_run=false`** at
17:15 UTC. The previously-running VM had been launched with `--dry-run` (serial:
"DRY RUN — no VMs killed"), so it never reaped.

The fresh `dry_run=false` watchdog **classified the active manual-backfill-campaign
VMs as zombies and DELETED them** (its heartbeat/shard-staleness heuristic flags a
slow-progressing-but-alive backfill as `zombie_stale_heartbeat`). It ran ~13 min
(17:15→17:28) before I caught it and deleted it; I then relaunched in `--dry-run`
(`vm-zombie-watchdog-20260623-171612`) so census is written WITHOUT reaping.

**9 VMs killed mid-run** (serial shows forced `systemd-shutdown Waiting for process:
python/bash` — not a clean self-delete; run.logs show active capture seconds before):

- `cefi-hyperliquid-2023-20260623-113700` (was capturing book_snapshot_5 @17:08)
- `cefi-hyperliquid-2025-20260623-113700`
- `cefi-hyperliquid-2026-20260623-113700` (was capturing book_snapshot_5 @17:06)
- `instr-backfill-sports-fixture-lineups-20260623-150323`
- `instr-backfill-sports-fixture-stats-20260623-153628`
- `instr-backfill-sports-matches-20260623-150038` (was processing @17:12)
- `instr-backfill-sports-matches-20260623-153418`
- `instr-backfill-sports-xg-20260623-164104`
- `instr-backfill-sports-xg-shots-20260623-165303`

(One more, `instr-backfill-sports-xg-20260623-153457`, SELF-completed cleanly —
`reason=cmd_ended` + `VM_SHUTDOWN_ON_COMPLETION` self-delete — NOT a wrong kill.)

`cefi-hyperliquid-2024` + `fs-backfill-20260622-230327` SURVIVED (still RUNNING).

## Why it matters

- Violates the HARD constraint "Do NOT restart/stop any running backfill VM."
- Interrupted 9 campaign backfills mid-run (cefi-hyperliquid 2023/2025/2026 +
  sports gap-fill VMs from the `instr-backfill-sports-*-20260623-15{00,34,36}` set
  tracked in `data_completion_to_100_all_ag_2026_06_21.md`).
- Mitigation: these backfills are idempotent + manifest-tracked — re-running fills
  the same gaps; no permanent data loss, only lost progress + the re-run cost. The
  manifest will show the affected (venue/data_type × date) cells as not-yet-captured.

## Root cause (two layers)

1. **Operator-action layer (mine):** relaunched the watchdog with reaping enabled
   during an active manual-backfill campaign. The watchdog MUST be `--dry-run`
   (report-only) while the campaign runs — its staleness heuristic cannot tell a
   slow campaign backfill from a true zombie. FIXED: now running `--dry-run`.
2. **Heuristic layer (code, latent):** `vm_zombie_watchdog.py` flags
   `zombie_stale_heartbeat` when a VM's heartbeat/shard hasn't advanced past the
   threshold (default hb 15m / shard 120m), which legitimately-slow backfills
   (cefi-hyperliquid S3 download, sports scrape) trip. The watchdog has no
   "campaign-mode" / launcher-class exemption for EPHEMERAL_BATCH backfills that
   are progressing-but-slow.

## Recommended decision

1. **Relaunch the 9 killed backfills** (idempotent; re-fills the manifest gaps).
   Recipe: the sports ones via `deployment-service/scripts/vm/launch-instruments-backfill-vm.sh`
   per (data_type, date-range) as in the plan's gap-fill item; the cefi-hyperliquid
   ones via their historical-backfill launcher. **Owner: the data-completion campaign
   agent** (do not relaunch a peer's campaign VMs without coordination — flagging here).
2. **Keep the watchdog in `--dry-run` for the duration of the manual-backfill
   campaign** (`launch-vm-zombie-watchdog.sh --dry-run`). Only re-enable reaping
   once the campaign drains.
3. **Code fix (latent, P2):** give `vm_zombie_watchdog.py` a campaign-mode flag or a
   per-lifecycle-class staleness budget so EPHEMERAL_BATCH backfills that emit
   PIPELINE_HEARTBEAT are not reaped while progressing. Owner: deployment-service
   infra agent.
