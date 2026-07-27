---
doc_type: issue
title:
  Orchestrator VM root disk hit 96% used — Docker image sprawl + a too-lax /tmp cleanup age, fixed with a live EBS
  resize and a systematic tmpfiles override
summary:
  Operator flagged 96% disk usage on the planning VM. Found two independent accumulation patterns — ~15 old dangling
  Docker images from repeated local builds (61GB total, modest real reclaim due to shared layers), and /tmp (a 2GB
  tmpfs) filled to 100% because the stock 30-day cleanup age never had a reason to fire against files that only live
  minutes to hours. Cleaned both, added a systematic 1-day /etc/tmpfiles.d override, and live-resized the root EBS
  volume 300GB to 500GB (96% to 58% used) for headroom. Operator decided to keep the larger volume rather than shrink
  back, given the mechanical risk of an EBS shrink and the still-tight post-cleanup margin at 300GB.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, vm, disk, ebs, docker, tmp, tmpfiles, infra]
related: []
created: 2026-07-27
last_updated: 2026-07-27
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: NA
drift_direction: advance-code
depends_on: []
resolved_by:
  interactive session 2026-07-27 — EBS resized live (no downtime), tmpfiles override shipped, operator confirmed keeping
  500GB
locked_by:
supersedes:
superseded_by:
source:
  Operator, 2026-07-27 — "96% of disk used on the vm planning, whats that on any of it temp any way we could be cleaning
  that us more systematically?"
---

# Orchestrator VM disk cleanup — 2026-07-27

## What I found

`df -h /` on the orchestrator VM (`i-0c9b283b31d6b5ca7`) showed 278/290 GB used (96%). Two independent, unrelated
accumulation patterns:

1. **Docker image sprawl** (`docker system df`): 21 images, 61.17 GB total, only 2 active. Repeated local builds of
   `market-tick-data-service` (4x, ~6GB each), `deployment-api` (3x, ~5GB each), and `unified-trading-library` (7x, ~4GB
   each) over the past ~2 weeks, with only the latest of each tag actually in use — every prior build left behind as an
   untagged (`<none>`) image. `docker image prune -f` recovered only ~5GB in practice (278G to 273G) despite reporting
   14GB "reclaimable" — most of these dangling images share underlying layers with the currently-tagged image, so the
   naive per-image size sum overstates what a prune actually frees.
2. **`/tmp` (a separate 2GB tmpfs, RAM-backed, NOT part of the root EBS volume) was at 100% used, 0 bytes free.** The
   stock `/usr/lib/tmpfiles.d/tmp.conf` ships a 30-day cleanup age (`D /tmp 1777 root root 30d`). This VM runs 17
   concurrent AO worker slots, each creating scratch files (mktemp dirs, QG artifacts, ad-hoc check outputs like
   `hitrate_*`/`baseline_*`) that are done within minutes to hours — the 30-day age meant the existing, already-active
   daily `systemd-tmpfiles-clean.timer` never had a reason to delete anything, letting scratch accumulate for weeks. All
   large files checked were 5.8-40h old and confirmed via `lsof +D /tmp` to not be held open by any running process
   before removal.

A full-disk `du` breakdown of the 17 slot worktrees was started but not completed this session (competing I/O with 17
active workers made it slow) — if disk pressure recurs, that's the next thing to check.

## The fix

- Docker: `docker image prune -f` (one-time; no automated prune wired up yet — this needs to be re-run periodically or
  built into whatever step produces these images, since nothing prevents the same accumulation recurring).
- `/tmp`: removed 11 confirmed-stale directories (~1.5GB, operator-executed directly since the local
  `block_destructive_commands.py` hook correctly blocks recursive `rm` for an agent — escalated per the hook's own
  instruction rather than working around it). Added `/etc/tmpfiles.d/tmp-aggressive-cleanup.conf`
  (`D /tmp 1777 root root 1d`) — a local override that takes precedence over the stock 30-day rule without editing the
  shipped file. The existing daily timer now actually does something; no new cron/timer needed.
- Root EBS volume: `aws ec2 modify-volume --volume-id vol-0b4f0237fa0f5cd0f --size 500` (region ap-northeast-1), then on
  the VM: `sgdisk -e /dev/nvme0n1` (relocate the backup GPT header to the new end-of-disk — required before `growpart`
  will succeed on a grown GPT disk), `growpart /dev/nvme0n1 1`, `resize2fs /dev/nvme0n1p1`. All live, no downtime.
  Result: 290GB to 484GB total, 278GB to 280GB used (unchanged, as expected), 96% to 58% used.
- **Gotcha**: `growpart` internally shells out to `sfdisk --list` and captures its output via a temp file under `/tmp` —
  with `/tmp` already full at the time of the first attempt, that capture silently failed, producing a confusing
  `failed [sfd_list:1]` error that had nothing to do with the partition table. Free `/tmp` space first if `growpart`
  fails this way.
- Cost: gp3 in ap-northeast-1 is
  $0.096/GB-month (confirmed via the AWS
  Pricing API, not assumed) — the +200GB is +$19.20/mo. Operator confirmed
  keeping the volume at 500GB rather than reverting to 300GB: EBS volumes can only grow live, never shrink via the same
  simple path (a shrink would need a full new-volume data migration on the live root disk); and even post-cleanup usage
  sat at 280GB, which would leave only ~20GB headroom in a 300GB volume — the same tight margin that caused this
  incident in the first place.

## Why it matters

96% disk usage on the single central orchestrator VM (the whole 17-slot fleet

- the operator's own dashboard depend on it) risks a much worse failure mode than slow performance — an out-of-space
  condition can corrupt SQLite writes, break git operations mid-commit, or crash the orchestrator service outright.
  Neither the Docker sprawl nor the `/tmp` policy would have self-corrected without direct intervention.

## Codex SSOTs

- `/codex/05-infrastructure/agent-orchestrator-deploy.md` — updated with the root EBS volume spec + a permanent "Disk
  hygiene" section covering this incident, the gotchas, and the ongoing Docker-prune follow-up.
