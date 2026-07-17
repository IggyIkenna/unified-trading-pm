---
doc_type: plan
title:
  AO host disk pressure — a second, independent cause of "worker left the task half-finished" (guard works, growth
  outpaces it)
summary: |
  The central orchestrator VM's root disk cycles 65%->95% every 6-18h, self-healing via vm-disk-guard.sh each time but
  never settling durably below ~60%. When it tops out, a worker's pytest/QG dies mid-task with
  "OSError: could not create numbered dir ... after 10 tries" — externally indistinguishable from the agent giving up,
  which is exactly the operator's "it finished some tasks and left others undone" symptom. This is INDEPENDENT of the
  AO dispatch bugs: fixing autospawn/dispatch would not have fixed it. Hardlink dedup is confirmed working (inode
  links=81), so dedup is not the gap — growth rate is. One remediation from the 2026-07-13 recurrence was never actually
  installed in production, which is the immediate lever.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, deployment-service]
scope: [engineer, admin]
tags: [infra, disk-pressure, slot-worktrees, uv-cache, vm-disk-guard, fleet-capacity, agent-orchestrator]
related:
  [
    issues/slot_venv_duplication_disk_pressure_2026_06_29.md,
    qg_host_adaptive_resource_governor_2026_07_14.md,
    ao_dispatch_hardening_2026_07_16.md,
    ../epics/orchestrator_master.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  - "operator 2026-07-16 — 'our current immediate scope is to make the AO work properly ... it finished some tasks and
    left others undone'; two human plans ruling — dispatch + infra, run in parallel"
  - "issues/slot_venv_duplication_disk_pressure_2026_06_29.md (2026-07-13 recurrence — 2.0 MB free / 100% used mid-QG)"
  - "AO issue-doc sweep 2026-07-16 — live SSM measurement of the real orchestrator VM (i-0c9b283b31d6b5ca7)"
---

# AO host disk pressure — the other half of "half-finished tasks"

> **Human plan — I execute it** (`assigned_vm: NA`). **Infra** craft, deliberately split from the backend-craft
> [`ao_dispatch_hardening_2026_07_16`](ao_dispatch_hardening_2026_07_16.md) so the two run in **parallel** (one plan =
> one agent = one craft). Ships via `quickmerge.sh --agent --files`.

## Why this is a separate root cause, not a footnote

The operator's symptoms have **two independent mechanisms**, and only one of them is a dispatch bug:

| Mechanism                                   | Symptom it produces                          | Owner                   |
| ------------------------------------------- | -------------------------------------------- | ----------------------- |
| R1 skip-blind spawn budget (`autospawn.py`) | workers idle in the loop **burning credits** | `ao_dispatch_hardening` |
| **Disk pressure killing workers mid-task**  | tasks **left half-finished**                 | **this plan**           |

Shipping the dispatch fixes alone would have left the second one live — we'd have watched tasks keep half-finishing and
concluded AO was still broken. The tell from the 2026-07-13 recurrence:

```
OSError: could not create numbered dir ... after 10 tries
```

That is a worker's `pytest`/`quality-gates.sh` step dying because the disk is full. From outside the box it looks
**identical to "the agent gave up"** — there is no signal that distinguishes them unless someone thinks to check
`df -h`. That ambiguity is why this went a month without being named as a cause.

## Measured live state (2026-07-16, real orchestrator VM via read-only AWS SSM)

Host: `agent-orchestrator-vm-1` / `i-0c9b283b31d6b5ca7` / `13.113.200.22` / ap-northeast-1 — **the actual host**, not a
dev box.

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/root       290G  203G   88G  70% /
```

`vm-disk-guard.sh` **is installed and firing** (`0 */6 * * *` + `@reboot`), and it **works every single time**:

```
2026-07-15T18:00:01Z  / at 81% (>= 80%) — vacuuming regenerable caches — done: 81% -> 71%
2026-07-16T06:00:01Z  / at 85% (>= 80%) — vacuuming regenerable caches — done: 85% -> 65%
2026-07-16T12:00:01Z  / at 70% (< 80%) — nothing to do
```

Observed guard cycles over 3 days: `95%→76%`, `90%→81%`, `86%→61%`, `81%→71%`, `90%→67%`, `81%→71%`, `85%→65%`.

**Read this carefully — the guard is not broken.** It fires, it succeeds, it reclaims 15–30 points every time. The
problem is the host **climbs back to 80–95% within 6–18h**, so between guard firings there is a window where a worker
can hit a full disk. Per-slot `.tabs` on the real VM: largest 18G (slot 4), 16G (slot 2), 9.9G (slot 5) — **no slot near
the pre-fix 27–29G outliers**, so the C1–C5 hardlink dedup fix genuinely worked (confirmed empirically: a shared
`_duckdb...so` at **inode 4620498, links=81**). Dedup is not the gap. **Growth rate vs guard cadence is the gap.**

## What the docs claim vs what the VM says (both measured 2026-07-16)

| Claim (in docs)                                                               | Measured on the real VM                                |
| ----------------------------------------------------------------------------- | ------------------------------------------------------ |
| `install-prune-uv-cache-cron.sh` remediation (from the 2026-07-13 doc)        | `crontab -l \| grep -i prune-uv` → **NONE_FOUND**      |
| `slot_venv…` banner: "RAM+CPU reservation governor live on the current fleet" | `qg-host-governor.sh --status` → **`MODE=token  K=2`** |

Both are the same class the 2026-07-16 sweep found repeatedly across the AO corpus: **code shipped, doc marked done,
deployment never verified.** Each took one command to check.

> **Scope note — the governor is NOT this plan's work.** `MODE=token` is not a bug: the reservation ledger is **Phase 3
> of [`qg_host_adaptive_resource_governor_2026_07_14`](qg_host_adaptive_resource_governor_2026_07_14.md)** (active, P1,
> infra) and simply has not shipped yet. That plan owns it; this plan does **not** duplicate it — it only corrects the
> `slot_venv…` banner that over-claims it as live, and records the measured `K=2` drift on the owning plan. Also note
> the governor gates **RAM/CPU admission, not disk** — anyone assuming it covers the disk axis is wrong.

## Todos

### Phase 1 — install the lever that already exists (P1)

- [x] [INFRA] P1. ✅ **DONE 2026-07-16 — installed, and a REAL bug found by running it.** Registered on
      `i-0c9b283b31d6b5ca7` (`0 */6 * * *`, verified in `crontab -l`). **But installing it was not enough — as written
      it would have done NOTHING, forever.** Running it as the cron actually runs it printed
      `uv not found on PATH — cannot     prune` and exited 1: cron's PATH is
      `/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin` and excludes `~/.local/bin`, where uv
      actually lives (`/home/ubuntu/.local/bin/uv`). A LOGIN shell finds it via `.profile`, so `command -v uv` succeeds
      when a human tests by hand and fails under the cron the script exists for — and it fails SILENTLY, exit 1 into a
      log nobody reads, so `crontab -l` would show it installed while the 11G cache was never touched. Fixed
      (`unified-trading-pm@88310f87a`): resolve uv via PATH → `~/.local/bin` → `~/.cargo/bin` → `/usr/local/bin` →
      `/opt/uv/bin`, invoke by absolute path, and list what was checked on failure. **Gate MET — measured, running it
      exactly as cron would (`env -i`, no login PATH):** `Removed 26449 files (826.9MiB)` /
      `[done] before_mb=10889 after_mb=10227 freed_mb=661 rc=0`; `.uv-cache` 11G → 10G; `df -h /` 213G→212G used,
      77G→78G free. This is the whole "installed ≠ working" lesson of the day in one todo: trusting `crontab -l` would
      have marked it done. ~~**Install `install-prune-uv-cache-cron.sh` on the central orchestrator VM.**~~ It was
      authored as the 2026-07-13 recurrence's remediation and **never installed in production** (verified 2026-07-16:
      `crontab -l | grep -i prune-uv` → NONE_FOUND on `i-0c9b283b31d6b5ca7`). This is the cheapest lever available — the
      uv-cache is 11G on that host and is regenerable. **Gate**: `crontab -l` on the VM shows the job; a subsequent run
      is visible in its log; `df -h /` measured before/after.
- [x] [INFRA] P1. ✅ **DONE 2026-07-16 — cadence `0 */6` → `0 */2` on `i-0c9b283b31d6b5ca7` (verified in `crontab -l`;
      guard re-run to prove it still works post-change: `15:19:46Z / at 74% (< 80%) — nothing to do`).** **Decided from
      the 3-day log, not guessed. Cadence, NOT threshold — and the data says why.** Max observed climb is **+19 points
      in 6h (~3.2/hour)**: `07-14 18:00 → 71%` post-vacuum, `07-15 00:00 → 90%`. And a **near-miss**: `07-16 00:00` read
      **79%** — ONE point under the trigger → "nothing to do" → it then flew blind to **85%** by 06:00. From a 79%
      no-fire reading, a worst-case climb reaches **~98%** before the next check. That is precisely the road to the
      2026-07-13 incident (2.0 MB free). **Why not lower the threshold to 70%** (the other option this todo offered):
      the guard vacuums IDLE-slot `.venv`s and clean off-slot worktrees, so firing more often means more `uv sync`
      rebuilds and slower worker boots — a real cost. A shorter cadence catches the SAME 80% level _sooner_ without
      firing more often: worst-case blind climb drops from +19 to **+6.4 points**. Replayed against the log: the 90%
      excursion would have fired at ~84%, the 85% one at ~81%. **Gate**: over the next 3 days the guard log should show
      no reading ≥ 88% and no "nothing to do" above ~76%. ~~**Decide + apply the `vm-disk-guard.sh`
      threshold/cadence.**~~ Current `80%` / `0 */6 * * *` lets the host reach **95%** between firings (measured).
      Either tighten the threshold (e.g. 70%) or shorten the cadence (e.g. every 2h), whichever the measured growth
      curve supports — the 3-day log above is the data. **Gate**: over a following 3-day window, peak `/` usage stays
      under a stated ceiling; cite the guard log.

### Phase 2 — close the ambiguity that hid this for a month (P1)

- [x] [INFRA] P1. ✅ **DONE 2026-07-16 — `agent-orchestrator@e7f70c8`. QG green: 1329 passed, basedpyright 0 errors.**
      Chose **prevention over labelling**: AutoSpawn now refuses to spawn onto a near-full disk and reports
      `disk_pressure` as the skip reason — so the disk is the ATTRIBUTED cause in the tick summary + activity feed at
      the moment it would have bitten, rather than a worker that boots, dies, and looks like a quitter. **Found on the
      way: the server had ZERO disk awareness anywhere** — no `df`, no `statvfs`, no no-space classification — so
      nothing _could_ have attributed it. That is why a month of half-finished tasks never pointed at the disk. **The
      dangerous failure mode was the fix itself**: too aggressive a threshold, or a probe that fails closed, halts the
      WHOLE fleet (no slot ever spawns) — far worse than the deaths it prevents. So: last-resort default (3% free ≈ 8.7G
      on the 290G VM, NOT a duplicate of vm-disk-guard's 80% janitor trigger — it fires only once the guard has already
      failed), the probe **fails OPEN** and never raises into the spawn path, and `0` disables it outright as an
      operator escape hatch. 3 of the 6 tests exist solely to pin that; injecting a fail-closed probe fails the
      fleet-halt guard. Reads `WORKSPACE_ROOT` not `/` — same volume on the fleet VM, but on a split host the workspace
      is the one a worker actually dies on. ~~**Make a disk-induced worker death distinguishable from an agent giving
      up.**~~ Today both look identical from the orchestrator's side, which is precisely why this went unnamed as a
      cause for a month. Emit a loud, attributable signal when a slot's disk is the reason a task died (e.g. a
      pre-flight `df` check at boot/heartbeat that flags the slot, or classify the `could not create numbered dir` /
      `No space left on device` signature into a distinct terminal reason rather than a generic failure). **Gate**: a
      simulated full-disk worker failure surfaces as a disk cause, not as a silent give-up.
- [x] [INFRA] P2. ✅ **DONE 2026-07-17 — MEASURED, and this todo was wrong on both of its factual claims. Gate met by
      correcting the record (the gate's own second branch); the two residual actions it exposes are operator-owned.**
      There are **THREE** caches on the dev host, not two: | cache | size | entries | last written | filesystem |
      verdict | | --- | --- | --- | --- | --- | --- | | `/active/uv-cache` | 30G | 6135 | **2026-07-08** | `nvme0n1p2` |
      **stale, pre-convention** | | `…/unified-trading-system-repos/.uv-cache` | 3.8G | 814 | **2026-07-17 (live)** |
      `nvme0n1p2` | **CURRENT** | | `/home/hk/.cache/uv` | 3.3G | 685 | **2026-07-17 (live)** | **`nvme0n1p1`** |
      **CURRENT, cross-fs** | - **Claim 1 — "`/active/uv-cache` (the live hardlink source)" is FALSE.** It is the FORMER
      source: newest `archive-v0` entry is **2026-07-08**, nine days stale, and **zero files in the workspace reference
      it** (the only hit is this plan). The live one is `.uv-cache`, which
      `scripts/quality-gates-base/base-service.sh:344` DERIVES
      (`UV_CACHE_DIR="${UV_CACHE_DIR:-${_uv_ws_common}/.uv-cache}"`). The convention superseded `/active/uv-cache` and
      nobody swept up. **I nearly got this backwards**: a sample file in `/active/uv-cache` showed `links=1`, which
      reads as "dead, reclaim it" — but that file was inside an abandoned `.tmp*` dir. Sampling the real `archive-v0`
      found **`links=81`** on `_duckdb…so`, the exact inode the `slot_venv_duplication` doc cites as dedup proof. It is
      stale but genuinely hardlinked; acting on the first sample would have argued for deleting 30G of live cache. -
      **Claim 2 — "both caches sit on the same filesystem so dedup is unaffected → cosmetic" does not cover the third,
      which this todo did not know about.** `/home/hk/.cache/uv` is uv's DEFAULT (`UV_CACHE_DIR` is unset in an
      interactive shell — `uv cache dir` confirms it) and sits on **`nvme0n1p1`, a different filesystem from the
      `/active` venvs it links into → hardlinks silently degrade to COPIES**. That is exactly failure mode **B2** named
      in [`slot_venv_duplication_disk_pressure_2026_06_29`](issues/slot_venv_duplication_disk_pressure_2026_06_29.md).
      QG runs are safe (base-service.sh exports the derived path); **hand-run `uv` is not**. And `nvme0n1p1` is the
      partition under pressure: **`/` at 84% (36G free)** vs `/active` at 53% (104G free). - **Scope kept honest**: the
      plan's disk thesis is about the AO VM (`i-0c9b283b31d6b5ca7`); this todo is the DEV host, so neither finding
      changes the VM verdict. **Deliberately took no destructive action** — 30G on the operator's own dev host, and
      CLAUDE.md's rule is that when the target contradicts its description you SURFACE it rather than proceed. Both
      follow-ups are recorded as operator-owned in `## Deferred work after 2026-07-17`. ~~**Reconcile the two coexisting
      uv caches.** The dev host runs BOTH `/active/uv-cache` (the live hardlink source) and
      `/active/unified-trading-system-repos/.uv-cache` — a drift from the documented single-cache convention. Harmless
      for dedup today (same filesystem, so hardlinks still work) but it means the documented SSOT path is not the one
      actually in use, which will mislead the next person who reasons about cache size.~~ **Gate**: one cache, or the
      convention doc updated to match reality — not both claiming to be the source.

### Phase 3 — correct the record (P2)

- [x] [REVIEW] P2. ✅ **DONE 2026-07-16.** The banner's "RAM+CPU reservation governor live on the current fleet" claim
      is contradicted by the measured `qg-host-governor.sh --status` → `MODE=token  K=2` on the real VM; recorded, with
      the note that the governor gates **RAM/CPU admission and does NOT cover the disk axis at all**, so it must never
      be cited as a disk mitigation. ~~**Fix the `slot_venv_duplication_disk_pressure_2026_06_29` banner's
      over-claim**~~ that the RAM+CPU reservation governor is "live on the current fleet" — measured `MODE=token K=2` on
      the real orchestrator VM. Note the governor is a **RAM/CPU admission** mechanism and does **not** cover the disk
      axis at all, so it must not be cited as a disk mitigation. **Gate**: the banner states measured runtime, not
      intended runtime.
- [x] [REVIEW] P2. ✅ **DONE 2026-07-16 — annotated on `qg_host_adaptive_resource_governor_2026_07_14`, no governor code
      touched from here** (that plan owns it; duplicating its work is the anti-pattern this sweep exists to stop).
      Recorded: live `qg-host-governor.sh --status` on `i-0c9b283b31d6b5ca7` returns **`MODE=token K=2`** while that
      plan's own text says bootstrap sets **K=6** — a silently-K=2 host runs at a third of intended concurrency, a real
      if quiet throughput tax on every ship from that VM. ~~**Record the measured governor drift on its owning plan**~~
      (`qg_host_adaptive_resource_governor_2026_07_14`): live `qg-host-governor.sh --status` on `i-0c9b283b31d6b5ca7`
      returns **`MODE=token K=2`**, while that plan's own text says bootstrap sets **K=6**. Either the bootstrap did not
      take on this host or something reset it — worth one check by the plan's owner. Annotate, **do not fix from here**
      (that plan owns the governor; duplicating its work is the anti-pattern this whole sweep exists to stop). **Gate**:
      annotation lands on that plan; no governor code touched by this plan.
- [x] [REVIEW] P2. ✅ **DONE 2026-07-16 — answered with the live SSM measurement.** Its ask ("has fleet growth outpaced
      hardlink-dedup?") → **No: dedup holds** (inode links=81; largest slot 18G vs the pre-fix 27–29G outliers), **the
      guard works every cycle** (7 firings/3 days, each reclaiming 15–30 points), and the residual gap is **growth rate
      between firings** — now addressed by the 2h cadence. Doc is `locked_by: live-defi-rollout` so it is NOT archived
      (needs `[unlock-plan]`, operator-only); todo carries the measurement instead of the question. ~~Flip the
      `slot_venv_duplication_disk_pressure_2026_06_29` open todo~~ — its ask ("re-verify the 2026-07-13 recurrence;
      determine whether fleet growth has outpaced hardlink-dedup") **was answered on 2026-07-16** by the live SSM
      measurement recorded above. Answer: **dedup holds (links=81, no 27–29G outliers); the guard works every cycle;
      growth rate between firings is the residual gap.** Note the doc is `locked_by: live-defi-rollout`, so it cannot be
      archived without an `[unlock-plan]` — flip the todo, leave the lock. **Gate**: the doc's open todo carries the
      measurement, not a question.

## Out of scope (named owners — nothing goes dark)

- **The RAM+CPU reservation governor itself** → `qg_host_adaptive_resource_governor_2026_07_14` (active, P1, infra).
  This plan annotates, never duplicates.
- **AO dispatch/autospawn/messaging** → `ao_dispatch_hardening_2026_07_16` (the parallel backend-craft plan).
- **Long-lived VM log backup** → `issues/long_lived_vm_logs_not_backed_up_2026_07_02` (verified accurate +
  operator-parked 2026-07-16; not a disk-capacity issue).

## Codex SSOTs

- `codex/05-infrastructure/per-tab-worktrees.md` — the per-slot clone model + hardlink/uv-cache convention.
- `codex/05-infrastructure/vm-launcher-runbook.md` — VM lifecycle + guard cron placement.
- `codex/06-coding-standards/quality-gates.md` — the QG host-governor contract (RAM/CPU, not disk).
- `codex/12-agent-workflow/async-wait-and-poll-discipline.md` — measured-verdict discipline for the Phase 1 gates.

## Progress Log

- **2026-07-16** — Created from the 20-doc AO issue-doc sweep (7 parallel code-verification agents). Disk pressure was
  re-measured **live on the real orchestrator VM** via read-only AWS SSM, not inferred from the dev host — the
  distinction matters, because the dev host and the fleet host have different disks and only the fleet host's numbers
  bear on the operator's symptom. Key correction to the prevailing story: **hardlink dedup is NOT the gap** (empirically
  confirmed working, inode links=81, no slot near the pre-fix outliers) and **the guard is NOT broken** (fires on
  schedule, reclaims 15–30 points every cycle). The gap is growth rate between firings, plus one remediation
  (`install-prune-uv-cache-cron.sh`) that was authored and **never installed**. Operator ruling 2026-07-16: two human
  plans, dispatch + infra, run in parallel. Deliberately scoped OUT the governor (owned by
  `qg_host_adaptive_resource_governor_2026_07_14`) after checking that plan first — creating a second governor plan
  would have been the exact duplicate-by-rediscovery failure this sweep documented.

## Progress Log — 2026-07-16 (executed)

- **Phase 1 — prune-uv cron: installed, and installing it was NOT enough.** Registered on `i-0c9b283b31d6b5ca7`
  (`0 */6`), then RAN it — `uv not found on PATH — cannot prune`. Cron's PATH excludes `~/.local/bin` where uv lives, so
  the script worked by hand and failed silently under the cron it exists for, exit 1 into a log nobody reads.
  `crontab -l` would have shown it installed while the 11G cache was never pruned. Fixed (`pm@88310f87a`) and re-run
  under a real cron env (`env -i`): **Removed 26449 files (826.9MiB), freed_mb=661**, cache 11G → 10G.
- **Phase 1 — guard cadence 6h → 2h** (`crontab` verified; guard re-run post-change: `74% (< 80%) — nothing to do`).
  Decided from the 3-day log: max climb **+19 points/6h**, and a near-miss where `07-16 00:00` read **79%** — one point
  under the trigger → "nothing to do" → flew blind to 85%. Cadence beats threshold here: a lower threshold would nuke
  idle-slot venvs more often (slower boots) for the same protection; a shorter cadence catches the same 80% level sooner
  and cuts worst-case blind climb to **+6.4 points**.
- **Phase 2 — the disk backstop** (`ao@e7f70c8`), above.
- ~~**Not done, deliberately**: the uv-cache dual-path reconcile (P2, cosmetic — both caches are on the same filesystem
  so dedup is unaffected; it is a documentation-vs-reality drift, not a disk-pressure driver).~~ **Superseded 2026-07-17
  — that framing was wrong on the facts** (see the Phase 2 todo). It was called cosmetic on the reasoning that "both
  caches are on the same filesystem"; measurement found a **third** cache, `/home/hk/.cache/uv`, on a **different**
  filesystem from the venvs it links into, on the partition that is actually full (`/` at 84% vs `/active` at 53%).
  Calling something cosmetic because two of three cases are benign is the failure this plan's own "what the docs claim
  vs what the VM says" table exists to catch — I did it to myself, one todo below that table.

## Progress Log — 2026-07-17

- **Phase 2 P2 (uv caches) — closed by measurement, and the todo was wrong twice.** Both of its factual claims failed:
  `/active/uv-cache` is **not** "the live hardlink source" (last written 2026-07-08, referenced by zero files) and the
  "same filesystem so it's cosmetic" reasoning did not cover the third, cross-filesystem cache it did not know existed.
  **Near-miss worth recording**: the first evidence I gathered — `links=1` on a sample file — pointed at "30G orphan,
  reclaim it". It came from an abandoned `.tmp*` dir. The real `archive-v0` shows `links=81`. One more command separated
  "delete 30G of live cache on the operator's dev host" from the right answer.

## Deferred work after 2026-07-17

| #   | Item                                                                            | State / why deferred                                                                                                                                                                                                                                                                                                                                                                | Blocked on      |
| --- | ------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 1   | **Reclaim the stale 30G `/active/uv-cache`**                                    | **Operator-owned.** Dead since 2026-07-08, zero references. Deleting it is SAFE for the 81 hardlinked venvs (hardlinks are equal citizens — the venv's copy survives; only blobs at `links=1` free space, so the real reclaim is < 30G). Your dev host, your call. `/active` is at 53%, so there is no pressure forcing it.                                                         | operator ruling |
| 2   | **`UV_CACHE_DIR` unset for interactive shells → cross-fs `/home/hk/.cache/uv`** | **Operator-owned (shell profile).** The B2 mode: hand-run `uv` links cross-filesystem → silent copies onto the 84%-full `/`. `slot_venv_duplication_disk_pressure_2026_06_29` already carries this as its own "Optional: if you run `uv` by hand a lot outside QG, add `UV_CACHE_DIR=<workspace-root>/.uv-cache` to your profile". QG is unaffected. Not mine to edit your profile. | operator ruling |

**Recommended NEXT: (2) before (1).** (2) is one line and stops new cross-fs copies landing on the partition that is
actually full; (1) frees space on the partition that isn't.
