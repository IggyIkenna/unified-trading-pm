---
title: QG Memory Governance — OOM Prevention for Parallel-Slot QGs
type: codex-coding-standard
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-15
owner: harsh-main
cadence: as-needed
verifier: any-agent
last_executed: 2026-05-15
---

# QG Memory Governance

> When 8 parallel slot agents each kick off `quality-gates.sh`, peak memory can
> exceed the dev box's physical RAM, triggering kernel OOM-killer and taking
> down VS Code + every worker session. This doc captures the guardrails landed
> 2026-05-15 and the knobs to relax them when capacity allows.

## The 2026-05-15 incident

- One Python process hit **79.7 GB RSS** before kernel OOM-killer fired.
  Trigger: `containerd` (Docker) needed more memory while a basedpyright
  langserver / pytest collection had already ballooned. Hardware: 93 GB RAM,
  8 GB swap.
- Smoking gun: `dmesg` shows
  `Out of memory: Killed process 2554667 (python) total-vm:84714188kB, anon-rss:79674232kB`.
- Blast radius: VS Code crashed, all 8 worker-slot Claude sessions terminated.
  Worktrees + branches survived; nothing data-side was lost.

## Three guardrails landed

| # | Where                                              | Knob                                | Default       | Purpose                                                  |
| - | -------------------------------------------------- | ----------------------------------- | ------------- | -------------------------------------------------------- |
| 1 | `scripts/quality-gates-base/base-service.sh`       | `QG_MEM_CAP`                        | `10G`         | per-subprocess hard memory cap via `systemd-run --user --scope` |
| 2 | `scripts/quality-gates-base/base-service.sh`       | `PYTEST_WORKERS`                    | `1`           | one xdist worker per QG (was `cpu_count // 4`)            |
| 3 | workspace `.vscode/settings.json` (not in git)     | `basedpyright.analysis.diagnosticMode` | `openFilesOnly` | IDE langserver does NOT crawl the whole 30-repo workspace |

### 1 — `systemd-run` mem cap

`base-service.sh` builds a `MEM_WRAP=(systemd-run --user --scope -p MemoryMax=$QG_MEM_CAP -p MemorySwapMax=0 --quiet --)`
array at startup and prepends it to every `pytest` and `basedpyright` invocation.

- Hard cap. Process exceeding it dies with exit 137 (SIGKILL by cgroup) — the
  QG fails cleanly, the box stays alive.
- `MemorySwapMax=0` is mandatory: without it the kernel swaps other processes
  out to keep the runaway alive, slowing everything down before the cap fires.
- Graceful fallback: if `systemd-run` is unavailable (CI image, container)
  `MEM_WRAP=()` empty and the commands run unwrapped — no behaviour change.

### 2 — `PYTEST_WORKERS=1` default

Previously each QG defaulted to `max(1, cpu_count // 4)` workers (4 on a 16-core
box). Eight slots × 4 workers × ~2-4GB peak = ~64-128 GB. The default is now 1.

Per-repo opt-in: set `PYTEST_WORKERS=N` in the repo's `scripts/quality-gates.sh`
**before** the `source base-service.sh` line if the repo is wall-clock-critical
and the dev box has memory headroom.

### 3 — IDE basedpyright scope

The VS Code basedpyright extension defaults to `diagnosticMode: "workspace"`
which crawls the entire workspace root. With 30+ sibling repos mounted as
worktrees, this can balloon to tens of GB.

Workspace `.vscode/settings.json` now sets:

```jsonc
{
  "basedpyright.analysis.diagnosticMode": "openFilesOnly",
  "basedpyright.analysis.useLibraryCodeForTypes": false,
  "basedpyright.analysis.exclude": [
    "**/.tabs/**", "**/.venv*/**", "**/node_modules/**",
    "**/build/**", "**/dist/**", "**/__pycache__/**",
    "**/.playwright-mcp/**"
  ]
}
```

These are workspace-local (the workspace root is NOT a git repo) — each dev box
needs them set independently. The QG-side basedpyright invocation
(`basedpyright $SOURCE_DIR/`) is unaffected — it already passes an explicit
source dir and is per-repo scoped.

## Relaxing the constraints later

Pick the knob that matches the bottleneck observed:

| Symptom                                                | Relax this                               | How                                                                                                     |
| ------------------------------------------------------ | ---------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| QG dies with exit 137 + "killed" message               | per-call `QG_MEM_CAP`                    | `QG_MEM_CAP=20G bash scripts/quality-gates.sh` (or set in repo's `quality-gates.sh` if recurring)        |
| Disable cap entirely (CI, big-mem host)                | `QG_MEM_CAP=0`                           | `QG_MEM_CAP=0 bash scripts/quality-gates.sh`                                                            |
| QG is wall-clock-bottlenecked on slow tests            | `PYTEST_WORKERS` in repo                 | add `PYTEST_WORKERS=4` BEFORE `source .../base-service.sh` line in the repo's `scripts/quality-gates.sh` |
| IDE basedpyright not finding cross-repo type errors    | switch back to workspace mode            | edit workspace `.vscode/settings.json` → `"basedpyright.analysis.diagnosticMode": "workspace"`           |
| Need parallel QG storms (eg dependency-alignment sweep)| stagger via `flock` (not yet implemented)| add `flock /tmp/qg.lock bash scripts/quality-gates.sh` wrapper in caller                                |

Order of relaxation when adding capacity (more RAM, fewer simultaneous slots):

1. Bump `PYTEST_WORKERS` to 2-4 in the wall-clock-critical repos first.
2. Bump `QG_MEM_CAP` to 16G or 20G if mem caps start firing under normal load.
3. Disable `MEM_WRAP` entirely (`QG_MEM_CAP=0`) only on hosts where the OOM is
   architecturally impossible (eg ≥256 GB RAM CI runners, or ≤2 concurrent slots).

## Cross-side guidance

Ikenna's side should run the same three guardrails — the `base-service.sh`
change auto-applies to every repo that sources it (no per-repo propagation
needed). The workspace `.vscode/settings.json` is per-dev-box and needs to be
set on every operator's workstation independently.

## Detection / verification

After landing or relaxing these settings, verify:

```bash
# Confirm MEM_WRAP is active (should print 9 elements when systemd-run usable):
( set -e; source unified-trading-pm/scripts/quality-gates-base/qg-common.sh
  source unified-trading-pm/scripts/quality-gates-base/base-service.sh \
    2>&1 | head -1 ) </dev/null || true
( cd <any-service-repo> && bash -x scripts/quality-gates.sh 2>&1 | head -50 | grep -i mem_wrap )

# Confirm pytest runs at PYTEST_WORKERS=1 (or whatever you set):
( cd <any-service-repo> && bash scripts/quality-gates.sh 2>&1 | grep -E '^-n [0-9]+' )

# Confirm IDE basedpyright is open-files-only (process should not balloon
# when you open a single Python file in a 30-repo workspace):
ps auxf | grep basedpyright-langserver | awk '{print $4, $5/1024/1024 " GB"}'
```

## Related SSOTs

- `codex/06-coding-standards/quality-gates.md` — main QG SSOT (links from here)
- `scripts/quality-gates-base/base-service.sh` — implementation
- `scripts/quality-gates-base/qg-common.sh` — `run_timeout` helper
- `scripts/quality-gates-base/quality-gates-service-template.sh` — repo stub template
