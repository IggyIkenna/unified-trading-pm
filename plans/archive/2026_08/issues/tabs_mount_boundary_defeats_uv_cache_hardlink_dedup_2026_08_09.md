---
doc_type: issue
title:
  .uv-cache sits outside .tabs/'s mount boundary — cache→venv hardlink dedup is still broken despite a prior DONE claim
summary: |
  While root-causing `ci_satellite_ao_dispatch_batch6_2026_08_08.md` item 10 (pnpm store hardlink dedup across
  per-slot worktree clones), found the identical failure mechanism for pnpm's store dir also applies to
  `UV_CACHE_DIR`: raw `ln` probes show `.tabs/<N>` <-> `.tabs/<M>` hardlinks succeed, but ANYTHING outside `.tabs/`
  (the default pnpm store, `unified-trading-pm/`, and — critically — `${WORKSPACE_ROOT}/.uv-cache` itself) fails
  with `EXDEV` (Invalid cross-device link), even though `stat -c %d` reports an identical device number for both
  sides. `host_root_disk_full_transient_2026_07_13.md`'s sub-item (b) claims "DONE 2026-08-08... root cause
  confirmed... fix: export UV_CACHE_DIR/UV_LINK_MODE=hardlink directly inside setup.sh" — but `.uv-cache` lives at
  `${WORKSPACE_ROOT}/.uv-cache` (a sibling of `.tabs/`, NOT inside it), so that fix cannot actually restore
  cross-slot hardlink dedup regardless of whether the env vars are correctly exported and honored — it will keep
  producing independent full copies per slot, silently, with no error.
status: resolved
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, disk-space, hardlink, uv-cache, pnpm-store, mount-boundary, per-tab-worktrees]
created: "2026-08-09"
author: agent (slot 24)
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
resolved_by: tabs_mount_boundary_defeats_uv_cache_hardlink_dedup-952b1ea6a09b (slot 6, 2026-08-09)
locked_by:
related:
  [
    /plans/active/issues/host_root_disk_full_transient_2026_07_13.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch6_2026_08_08.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
source: [ci_satellite_ao_dispatch_batch6_2026_08_08.md item 10 (agent slot 24, 2026-08-09)]
depends_on: []
---

# .uv-cache sits outside .tabs/'s mount boundary — cache→venv hardlink dedup is still broken despite a prior DONE claim

> **🟢 ARCHIVED 2026-08-09 — COMPLETE.** Sole todo shipped + verified (real `uv sync` shows `nlink=2`). See Progress Log
> below. `/plans/active/issues/host_root_disk_full_transient_2026_07_13.md`'s sub-item (b) verdict corrected in the same
> session; codex SSOT updated at `/codex/05-infrastructure/per-tab-worktrees.md` § "Shared uv cache".

## What I found

Investigating `ci_satellite_ao_dispatch_batch6_2026_08_08.md` item 10 (pnpm store hardlink dedup), I isolated the root
cause via raw `ln` probes rather than pnpm-specific debugging:

```
$ ln <scratchpad-file> .tabs/24/deployment-ui/dst.txt
ln: Invalid cross-device link                                    # FAILS

$ ln .tabs/24/probe_src.txt .tabs/2/probe_dst.txt
(exit 0)                                                          # SUCCEEDS — same .tabs/ boundary

$ ln ~/.local/share/pnpm/probe_src.txt .tabs/24/deployment-ui/probe_dst.txt
ln: Invalid cross-device link                                    # FAILS — pnpm's default store

$ ln unified-trading-pm/probe_pm.txt .tabs/24/probe_from_pm.txt
ln: Invalid cross-device link                                    # FAILS — a sibling repo clone

$ ln ${WORKSPACE_ROOT}/.uv-cache/probe_uv.txt .tabs/24/probe_from_uvcache.txt
ln: Invalid cross-device link                                    # FAILS — the uv-cache fix's own target dir
```

`stat -c %d` reports the SAME device number for every path above (this host presents each top-level directory —
`.tabs/`, `unified-trading-pm/`, `~/.local/share/pnpm`, `${WORKSPACE_ROOT}/.uv-cache` — as its own bind-mount/gofer
instance with a normalized/shared device id, but the kernel's `link()` syscall still refuses to cross the real mount
boundary between them). Anything physically located INSIDE `.tabs/` can hardlink to any other location inside `.tabs/`
(proven both slot↔slot and via a probe store placed at `.tabs/.pnpm-store`); anything outside `.tabs/` cannot reach into
it.

`host_root_disk_full_transient_2026_07_13.md` sub-item (b) states (2026-08-08): "root cause: CONFIRMED REGRESSION to
zero cache→venv hardlink dedup... fix: `export UV_CACHE_DIR=...; export UV_LINK_MODE=hardlink` directly inside
`scripts/setup.sh`... DONE." That fix addresses "the exported env var wasn't reaching the install call" — a real and
separate bug — but does NOT address the mount-boundary problem, because `UV_CACHE_DIR` is set to
`${WORKSPACE_ROOT}/.uv-cache`, which sits at the workspace root as a SIBLING of `.tabs/`, not inside it. Even with the
env vars now correctly exported and honored, every `uv sync` into a `.tabs/<N>/<repo>/.venv` will still hit the same
`EXDEV` → silent-copy-fallback this doc's own earlier language already names as the failure signature.

## Why it matters

- The `.venv` footprint (previously measured "150-200G... could shrink dramatically for free") is very likely STILL not
  deduped across the fleet's 16 slots, despite the doc's own DONE marker — a false-green on a real,
  previously-quantified disk-waste finding.
- This is the exact same failure class my sibling investigation (pnpm store, `ci_satellite_ao_dispatch_batch6` item 10)
  found and fixed by relocating the store INSIDE `.tabs/` instead of just re-exporting env vars — the fix pattern that
  worked there (move the shared cache/store physically under `.tabs/`) should transfer directly here.
- Nobody would discover this without an inode/nlink check (or a raw `ln` probe) — `uv sync`/`pnpm install` both exit 0
  and print nothing about the fallback; disk usage is the only visible symptom, and it grows slowly enough to not
  obviously look like a regression.

## Recommended decision

Relocate `UV_CACHE_DIR` to a path INSIDE `.tabs/` (e.g. `${WORKSPACE_ROOT}/.tabs/.uv-cache`, mirroring this session's
pnpm fix of `${WORKSPACE_ROOT}/.tabs/.pnpm-store`) in every place it's currently derived (`base-service.sh`,
`install-uv-cache-shell-env.sh`, `prune-uv-cache.sh`), then re-run the same before/after inode/nlink verification
`host_root_disk_full_transient_2026_07_13.md` already used (1,800-file `.so` sample) to confirm dedup is actually
restored — not just that the env vars are set.

- [x] ✅ [INFRA] P2. Relocate `UV_CACHE_DIR` from `${WORKSPACE_ROOT}/.uv-cache` to `${WORKSPACE_ROOT}/.tabs/.uv-cache`
      (inside the `.tabs/` mount boundary) in `base-service.sh`, `install-uv-cache-shell-env.sh`, and
      `prune-uv-cache.sh`; re-verify cross-slot `.venv` hardlink dedup via a real inode/nlink sample (not just an
      env-var check), and update `host_root_disk_full_transient_2026_07_13.md`'s sub-item (b) DONE claim with the
      corrected verdict. (repo: unified-trading-pm) — **DONE 2026-08-09.**

## Progress Log

- **2026-08-09 (infra, `tabs_mount_boundary_defeats_uv_cache_hardlink_dedup-952b1ea6a09b`).** Shipped the relocation in
  all 3 named files plus 2 adjacent same-root-cause spots the todo didn't name but the fix would be incomplete without:
  `install-prune-uv-cache-cron.sh` (bakes the stale path into its cron line via `--cache-dir`, which would have silently
  overridden `prune-uv-cache.sh`'s own corrected default) and `agent-orchestrator/server/tmux_spawn.py` (the AO
  spawn-time export every worker session — including this one — inherits; same sibling-of-`.tabs` derivation, same bug).
  `unified-trading-pm@2c028dee9d`, `agent-orchestrator@9ae79d6`. **Verified two ways**: (1) a raw `ln` probe from the
  new `.tabs/.uv-cache` into a live slot dir succeeds (same inode) — confirms the location is genuinely inside the mount
  boundary; (2) a real `uv sync` of `unified-api-contracts` against the relocated cache — **10/10 sampled `.so` files
  show `nlink=2`** (fleet-wide baseline was `nlink=1`, 1,800/1,800, per the 2026-08-08 investigation this fix corrects)
  — cache→venv hardlink dedup is genuinely restored, not just configured. Also corrected
  `host_root_disk_full_transient_2026_07_13.md`'s sub-item (b) verdict + updated the codex SSOT
  (`/codex/05-infrastructure/per-tab-worktrees.md` § "Shared uv cache") per this doc's own recommended decision.
