---
doc_type: codex-ssot
title: Shared-host /tmp tmpfs capacity — root cause + routing convention + reaper
summary: >-
  SSOT for the shared orchestrator host's `/tmp` mount being a fixed RAM-backed tmpfs that has repeatedly hit 100% and
  broken unrelated pytest runs fleet-wide with "No space left on device". Root cause is ACCUMULATION of orphaned
  scratch across at least two distinct offender classes (not sizing — the tmpfs was already resized ~4x and still
  saturates): (1) large one-off parquet scratch from instruments-service writers, and (2) — added 2026-08-21 —
  scratch from `PrivateTmp=yes` systemd units (e.g. codex-bridge.service) whose whole process tree writes into an
  isolated `/tmp` namespace the original reaper couldn't see. Fix at the root — (1) the recurring instruments-service
  writers route their large parquet staging to a non-tmpfs scratch dir (`$HOME/.cache/instruments-scratch`,
  mirroring the `$HOME/.cache/qg-tmp` scratchpad convention), and (2) a liveness-gated TTL reaper
  (`cleanup-stale-tmp-parquet-scratch.sh` + cron, now sub-hourly) reclaims orphans on the root disk, any residual
  one-off `/tmp` parquet scratch, AND — via a second, name-unrestricted sweep — the entire contents of any discovered
  `PrivateTmp` service namespace. Includes the sizing decision rationale (RAM headroom check) and the
  multi-agent-safety ownership rule for cleanup.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [infra, tmpfs, /tmp, disk-space, shared-host, pytest, scratch, parquet, capacity]
related:
  [
    /plans/active/issues/host_tmp_tmpfs_full_breaks_pytest_write_2026_08_09.md,
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch15_2026_08_10.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-08-10
authoritative_for: [
    shared-host /tmp tmpfs capacity root cause + the large-parquet-scratch routing convention + the TTL reaper that
    enforces it,
  ]
referenced_by:
  [
    /plans/active/issues/host_tmp_tmpfs_full_breaks_pytest_write_2026_08_09.md,
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch15_2026_08_10.md,
  ]
owner:
last_reviewed: 2026-08-21
code_refs:
  [
    instruments-service/scripts/enumerate_expected_universe.py,
    instruments-service/scripts/reconcile_correct_legacy_blank_misflips_cefi_2026_05_13.py,
    unified-trading-pm/scripts/dev/cleanup-stale-tmp-parquet-scratch.sh,
  ]
---

# Shared-host `/tmp` tmpfs capacity

> **Purpose.** A fresh agent hitting spurious "No space left on device" pytest failures should be able to (a) recognize
> this is the host-wide `/tmp` tmpfs, (b) know the root cause is accumulation of large one-off parquet scratch, NOT a
> code defect, and (c) know the standing fix — routing + the reaper — so they don't re-derive it or try a blind tmpfs
> resize.

## The mount

`/etc/fstab` on the shared orchestrator host (`planning` VM):

```
tmpfs /tmp tmpfs rw,nosuid,nodev,noatime,size=8G,mode=1777 0 0
```

- **RAM-backed, fixed ceiling, independent of the root disk.** `df -h /tmp` reads the tmpfs; `df -h /` reads the
  (healthy, ~175G-free) root partition. A full `/tmp` gives "No space left on device" that is indistinguishable from a
  real test regression unless you check `df -h /tmp` specifically.
- **Sizing history (decisive against resize-only fixes).** The tmpfs was measured at **2.0G** on 2026-07-27 and was
  resized to **8.0G** by 2026-08-09 — a ~4x increase — and STILL saturated to 100% on 2026-08-09. The pattern is
  accumulation of large one-off scratch, not a fixed-size-too-small problem. A further raise would trade real RAM (only
  ~1.6–3.3G genuinely free on the host, ~19G available counting reclaimable buff/cache) for headroom that history says
  still gets consumed. **Do not resize `/tmp` as a first-line fix** — route the writers + reap instead (below).

## Root cause

The recurring large `/tmp` consumers are **one-off parquet scratch files** — `enum-univ-*`, `enum-shard-*`,
`cefi-corrector-*`, `avail_idx*`, `cefi_availability_index*` — written by instruments-service scripts
(`enumerate_expected_universe.py`, `reconcile_correct_legacy_blank_misflips_cefi_2026_05_13.py`) via
`tempfile.NamedTemporaryFile(delete=False)` (default `tempfile.gettempdir()` = `/tmp`). Each file is 150MB–2.8GB. The
cleanup lives in a `finally: os.unlink(...)` — so a SIGKILLed/interrupted/preempted run orphans the file permanently on
the RAM-backed tmpfs. Confirmed live: on 2026-08-09 two `enum-univ-defi-*.parquet` at 2.8G each (5.6G of the 8G tmpfs);
on 2026-08-10 the largest consumers had fully turned over (new `enum-univ-prediction-*`, `repro-venv` 808M, several
~198M parquets) — the SAME unmanaged-accumulation pattern recurring with different actors.

## Fix — route + reap (2026-08-10)

### 1. Route the recurring writers off the tmpfs (root fix)

`enumerate_expected_universe.py` and `reconcile_correct_legacy_blank_misflips_cefi_2026_05_13.py` now stage their large
one-off parquet files under **`$HOME/.cache/instruments-scratch`** (root partition) instead of `/tmp`, via a
module-level `_scratch_dir()` helper that:

- defaults to `${HOME}/.cache/instruments-scratch` (mirrors the workspace's `${HOME}/.cache/qg-tmp` scratchpad
  convention for QG scratch),
- is overridable via `--scratch-dir` (CLI) or `$INSTRUMENTS_SCRATCH_DIR` (env),
- creates the dir on demand, and
- is applied to every `tempfile.NamedTemporaryFile(...)` large-parquet call in both scripts (5 sites in enumerate, 2 in
  reconcile).

This means even a SIGKILLed run orphans the parquet on the root disk where it is harmless to pytest (and reclaimed by
the reaper below), never on the RAM-backed tmpfs.

### 2. Reap orphans + residual one-off `/tmp` scratch (belt-and-suspenders)

`unified-trading-pm/scripts/dev/cleanup-stale-tmp-parquet-scratch.sh` (cron:
`install-cleanup-stale-tmp-parquet-scratch-cron.sh`) runs TWO sweeps per invocation:

**Sweep 1 (original)** — both:

- `${HOME}/.cache/instruments-scratch` — orphans left behind by a SIGKILLed run,
- `/tmp` — any one-off ad-hoc parquet scratch that still defaults there,

for the offender name-globs (`*.parquet`, `enum-univ-*`, `enum-shard-*`, `cefi-corrector-*`, `cefi-corrector-out-*`,
`avail_idx*`, `cefi_availability_index*`, `repro-*`, `regen-ldr-plans-*`, `node-compile-cache`, `actionlint*`,
`kalshi_*.json`), **liveness-gated** (never touches a file with an open handle — `fuser`), TTL default 6h, dry-run
supported. Deliberately excludes `pytest-of-*` (owned by `cleanup-stale-qg-tmp.sh`) and `claude-*`
(`cleanup-stale-claude-session-tmp.sh`).

**Sweep 2 (added 2026-08-21, distinct offender class)** — a `PrivateTmp=yes` systemd unit
(e.g. `codex-bridge.service`, a Codex/Luna-backed agent bridge) gives its whole process
tree an isolated `/tmp` namespace bind-mounted at the host path
`/tmp/systemd-private-<boot-id>-<unit>-<random>/tmp`. Every descendant of that unit's
`/tmp` writes lands there instead of the shared `/tmp` — including full
`quickmerge --isolated` worktrees (`qm-iso-*`), `prek` scratch, and QG scratch, whenever
that unit's children run those tools (e.g. an agent session shipping code). Sweep 1 never
sees these paths — they're invisible unless you glob for `systemd-private-*` dirs
specifically. Confirmed live 2026-08-21: one such dir alone held the ENTIRE 8G tmpfs
(17895 files, accumulated over the unit's 18h uptime with zero reaping) and caused live
`sqlite3.OperationalError: database or disk is full` on `orchestrator.service`. Sweep 2
discovers every `systemd-private-*/tmp` root under `/tmp` and reaps its ENTIRE contents by
age + liveness — no name-glob restriction, because that root is by construction nothing
but transient scratch for one unit's child processes (enumerating every tool a
Codex-driven session might invoke would be permanent whack-a-mole); `tmux-*` is the one
denylisted name (a live tmux server socket dir, not scratch). TTL default 60min via
`--private-tmp-min-age`, same liveness gate as sweep 1.

**Root privilege requirement (2026-08-21)**: the outer `systemd-private-*` directory is
`drwx------ root:root` — confirmed live that the non-root `ubuntu` operator account
(the ONLY account this script's own cron is allowed to install under, per its root-refusal
guard) cannot traverse into it at all, so sweep 2 is a structural no-op under the
operator's own crontab. Sweep 2 can only ever do anything when this script runs as root.
The fix is a SEPARATE root-owned systemd timer + oneshot service invoking this same
script (reusing its liveness-gated sweep-2 logic, not systemd-tmpfiles' pure-mtime
cleanup) — NOT a change to the operator cron's privilege level. See
`/plans/active/issues/ao_tmp_tmpfs_full_sqlite_disk_full_errors_2026_08_21.md` for the
install status.

**Cadence (revised 2026-08-21)**: the cron interval is now 15 minutes by default (was 6h)
— sweep 1's own 6h min-age threshold means most 15-min firings are cheap no-ops for that
class, but sweep 2 needs sub-hourly cadence given how fast a `PrivateTmp` unit can
accumulate. `install-cleanup-stale-tmp-parquet-scratch-cron.sh --interval N` accepts N<60
(minute-of-hour cron syntax) or N>=60 (original hour-granularity syntax, kept for any
existing hour-multiple install). This governs the operator-level sweep-1 cron; the
root-owned sweep-2 timer (above) has its own, separately-installed cadence.

### 3. Why not just resize (the sizing decision)

`free -h` at fix time: 30Gi total, ~11Gi used, ~3.3Gi free, ~17Gi buff/cache, ~19Gi available — i.e. headroom exists
only by counting reclaimable cache, and swap is already in use. Combined with the 2G→8G resize history still saturating,
a resize is a poor trade: it spends real RAM for headroom that the accumulation pattern will re-fill. The correct fix is
routing (stops the large files from ever landing on the tmpfs) + reaping (bounds what does land there).

## Multi-agent-safety ownership rule

The reaper is **liveness-gated** precisely so it never deletes another slot's in-flight scratch: it skips any file with
an open handle, regardless of age. Manual cleanup of a currently-large `/tmp` file must confirm genuine ownership (is
the writing process still alive? — check `lsof`/`fuser` first) per the multi-agent-safety HARD RULE against touching
another slot's untracked/in-flight state — do not blind-delete. See
`/plans/active/issues/host_tmp_tmpfs_full_breaks_pytest_write_2026_08_09.md` for the incident + ownership-audit caution.

## Precedent + coverage

This doc is the SSOT for the `/tmp` tmpfs capacity class. Prior iterations on the same class:
`/plans/archive/issues/shared_host_tmp_tmpfs_exhaustion_2026_07_08.md` (QG `TMPDIR`→`${HOME}/.cache/qg-tmp`),
`/plans/archive/issues/shared_host_tmp_tmpfs_exhaustion_2026_07_26.md` (claude-session cleanup),
`/plans/archive/issues/shared_host_tmp_tmpfs_full_2026_07_26.md` (root-disk + manifest-consolidate reaper). The systemd
`tmp-aggressive-cleanup.conf` (`D /tmp 1777 root root 1d`) remains as a last-resort 24h age sweep; the parquet reaper's
6h TTL + liveness gate is the tighter, safer primary.
