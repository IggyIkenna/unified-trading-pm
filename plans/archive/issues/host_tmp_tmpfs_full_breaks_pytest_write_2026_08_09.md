---
doc_type: issue
title:
  "Shared-host /tmp (tmpfs, 8GB) hit 100% full — breaks pytest across every slot, distinct from the root-disk issue"
summary:
  "While running deployment-service quality-gates.sh from slot 22, 4 unrelated tests (test_vm_launcher_scripts.py
  TestCanonicalMigrationStallDetection/TestCefiFundingTimestampFixStallDetection) failed with 'write error: No space
  left on device'. `df -h /tmp` showed tmpfs 8.0G, 100% used, 0 available — confirmed via a clean-tree stash-and-retest
  that the SAME two tests pass when tmpfs has headroom, so this is host-wide capacity, not a test/code defect. `du -sh
  /tmp/* | sort -rh` (read-only, nothing deleted) shows the largest consumers are OTHER slots' scratch parquets: two
  `enum-univ-defi-*.parquet` at 2.8G each (5.6G of the 8G total), plus `enum-univ-catalog-prediction-*.parquet` (282M
  x2), `repro-venv` (808M), several `cefi-corrector-*`/`regen-ldr-plans-*` scratch files — none of these are mine, and
  per the multi-agent-safety HARD RULE against touching another slot's untracked/dirty state, I did not delete anything.
  Distinct from `plans/archive/2026_08/issues/host_root_disk_full_transient_2026_07_13.md` (that issue is the root
  filesystem `/dev/root`, currently a healthy 75% used / 175G free; THIS issue is the separate RAM-backed `/tmp` tmpfs
  mount, which is a fixed 8GB ceiling that doesn't grow with root-disk headroom — a distinct capacity class needing its
  own fix (either raise the tmpfs size, or route large scratch parquets to a non-tmpfs scratch dir)."
status: open
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, disk-space, tmpfs, host-contention, capacity, pytest]
related:
  [
    /plans/archive/2026_08/issues/host_root_disk_full_transient_2026_07_13.md,
    /plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-08-09
last_updated: 2026-08-09
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
context_scope:
  [
    unified-trading-pm/scripts/dev/cleanup-stale-tmp-parquet-scratch.sh,
    /codex/05-infrastructure/shared-host-tmp-tmpfs-capacity.md,
    /plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md,
  ]
source: slot 22, deployment-service QG run during cross_cutting_satellite_ao_dispatch_batch5-77d480c19d08, 2026-08-09
---

> **📦 ARCHIVED 2026-08-22 (archival pass 2)** — BRIDGE resolved: both todos done 2026-08-10; the gating parent
> plan (`infra_satellite_ao_dispatch_batch15_2026_08_10.md`) has itself since archived
> (`plans/archive/2026_08/infra_satellite_ao_dispatch_batch15_2026_08_10.md`), reaching the terminal status
> the bridge was waiting on. Kept as a historical record.
# Shared-host /tmp tmpfs full — breaks pytest fleet-wide

## What I found

`df -h /tmp` at 2026-08-09 ~13:50 UTC: `tmpfs 8.0G 8.0G 0 100% /tmp`. This is RAM-backed and capped at 8GB regardless of
the (healthy, 175G-free) root disk. Any test or script that writes a scratch file to `/tmp` fails with
`write error: No space left on device` while this holds — confirmed live on 4 `deployment-service` tests unrelated to my
own diff (verified via `git stash` + re-run on a clean tree: same 2 tests passed moments before, then failed again once
tmpfs re-saturated).

`du -sh /tmp/* | sort -rh` (read-only): largest consumers are scratch parquets from OTHER slots' in-flight sessions
(`enum-univ-defi-*.parquet` 2.8G x2, `enum-univ-catalog-prediction-*.parquet` 282M x2, `repro-venv` 808M,
`cefi-corrector-*`/`regen-ldr-plans-*` scratch files) — not deleted, per the multi-agent-safety rule against touching
another slot's untracked state without confirming it's genuinely dead.

## Why it matters

Any agent's `quality-gates.sh` run (pytest writes tmp fixtures/artifacts) can spuriously fail with a real host-wide "No
space" error indistinguishable from a genuine test regression unless the agent thinks to check `df -h /tmp` specifically
(not just `df -h /`, which stays healthy) — a likely source of wasted debugging cycles fleet-wide.

## Recommended decision

Either (a) raise the `/tmp` tmpfs size (if RAM headroom allows — check `free -h` at decision time), or (b) audit whether
the large one-off scratch parquets (`enum-univ-*`) are genuinely needed post-run and should target a non-tmpfs scratch
dir (mirrors the workspace's own scratchpad-directory convention for agent sessions) instead of `/tmp`, or (c) both.
Whoever owns infra should also confirm whether any of the currently-large `/tmp` files are actually orphaned (owning
process long-dead) vs a live session's genuine in-flight scratch — only then is deletion safe.

## Todo

- [x] ✅ [INFRA] P1. **Determine whether `/tmp` tmpfs sizing is fixed-too-small or the real problem is scratch files not
      being cleaned up post-run**, and fix at the root (raise tmpfs size and/or route large one-off parquet scratch
      writes to a non-tmpfs path). Repo: unified-trading-pm (host/VM config) or wherever the tmpfs mount is provisioned.
      **Relevant prior history (added 2026-08-10, plan_reconciler infra shard, agt-716973)**:
      `shared_host_home_filesystem_full_2026_07_26.md` documents this SAME `/tmp` tmpfs-full symptom recurring at least
      4 times between 2026-07-27 and 07-31, at a measured **2.0G total tmpfs** size then — vs. this doc's 2026-08-09
      reading of an **8.0G total tmpfs**. The tmpfs was already resized ~4x between those dates and still saturates —
      suggestive evidence toward "cleanup problem, not sizing problem." That doc also documents a workaround (point
      `TMPDIR`/`TF_DATA_DIR` at a short path under `/home/ubuntu/` instead of `/tmp`) worth checking before this todo's
      own investigation starts from scratch. — **DONE 2026-08-10 (slot-20,
      infra_satellite_ao_dispatch_batch15-fc54cb24200b).** Verified the "cleanup problem, not sizing problem" read live:
      tmpfs already resized 2G→8G (4x) and still saturates; `free -h` ~3.3G genuinely free → resize is a poor trade and
      prior operator rulings (07-08/07-26) kept the mount resize out of scope. Fixed at the root by ROUTING the
      recurring writers off the tmpfs (instruments-service@bc36e4a5: enum-univ-_/enum-shard-_/cefi-corrector-* parquets
      now stage under `$HOME/.cache/instruments-scratch` on the root disk, `_scratch_dir()` helper + `--scratch-dir`/
      `$INSTRUMENTS_SCRATCH_DIR` override) + a liveness-gated TTL reaper
      (`unified-trading-pm/scripts/dev/cleanup-stale-tmp-parquet-scratch.sh` + cron installer, PM@f6af641115) + codex
      SSOT `/codex/05-infrastructure/shared-host-tmp-tmpfs-capacity.md`. `df -h /tmp` 8.0G 3.1G used — no plausible path
      to 100% under normal fleet load with the recurring offenders routed off the tmpfs.
- [x] ✅ [INFRA] P2. **Audit the specific large `/tmp/enum-univ-*` files for genuine ownership** (is the writing process
      still alive?) before any cleanup — do not blind-delete another slot's WIP. — **DONE 2026-08-10 (slot-20,
      infra_satellite_ao_dispatch_batch15-fc54cb24200b).** Ownership audit folded into the fix per the plan: (1)
      verified live via `lsof` that the 2026-08-09 enum-univ-defi 2.8G pair + today's largest consumers (`repro-venv`
      808M, `cefi_availability_index.parquet`, `avail_idx.parquet`) have ZERO open handles — orphaned (writing process
      dead), but nothing was blindly deleted; (2) the shipped reaper is liveness-gated (never touches a file with an
      open handle — `fuser`) so it can only reclaim genuinely-dead scratch, satisfying the ownership-audit caution as a
      standing mechanism rather than a one-time check.

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (3 entries).
- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:2a2570b34efd7403]: content fully resolved — both
  todos already `[x]` DONE, no prose-only remaining work found on full read. Not archived: `archive_exempt: true`
  (own frontmatter) blocks the ritual pending the referencing parent plan
  (`infra_satellite_ao_dispatch_batch15_2026_08_10.md`) reaching a terminal status — a standing, documented bridge,
  not overridden here (out of this skill's mandate; route to `/archive-candidates-audit` if that parent plan has
  since archived).
- **context-scout 2026-08-20**: refreshed context_scope (3 entries).
