---
scope: [engineer, admin]
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

> When 8 parallel slot agents each kick off `quality-gates.sh`, peak memory can exceed the dev box's physical RAM,
> triggering kernel OOM-killer and taking down VS Code + every worker session. This doc captures the guardrails landed
> 2026-05-15 and the knobs to relax them when capacity allows.

## The 2026-05-15 incident

- One Python process hit **79.7 GB RSS** before kernel OOM-killer fired. Trigger: `containerd` (Docker) needed more
  memory while a basedpyright langserver / pytest collection had already ballooned. Hardware: 93 GB RAM, 8 GB swap.
- Smoking gun: `dmesg` shows `Out of memory: Killed process 2554667 (python) total-vm:84714188kB, anon-rss:79674232kB`.
- Blast radius: VS Code crashed, all 8 worker-slot Claude sessions terminated. Worktrees + branches survived; nothing
  data-side was lost.

## Three guardrails landed

| #   | Where                                          | Knob                                   | Default         | Purpose                                                         |
| --- | ---------------------------------------------- | -------------------------------------- | --------------- | --------------------------------------------------------------- |
| 1   | `scripts/quality-gates-base/base-service.sh`   | `QG_MEM_CAP`                           | `10G`           | per-subprocess hard memory cap via `systemd-run --user --scope` |
| 2   | `scripts/quality-gates-base/base-service.sh`   | `PYTEST_WORKERS`                       | `1`             | one xdist worker per QG (was `cpu_count // 4`)                  |
| 3   | workspace `.vscode/settings.json` (not in git) | `basedpyright.analysis.diagnosticMode` | `openFilesOnly` | IDE langserver does NOT crawl the whole 30-repo workspace       |

### 1 — `systemd-run` mem cap

`base-service.sh` builds a
`MEM_WRAP=(systemd-run --user --scope -p MemoryMax=$QG_MEM_CAP -p MemorySwapMax=0 --quiet --)` array at startup and
prepends it to every `pytest` and `basedpyright` invocation.

- Hard cap. Process exceeding it dies with exit 137 (SIGKILL by cgroup) — the QG fails cleanly, the box stays alive.
- `MemorySwapMax=0` is mandatory: without it the kernel swaps other processes out to keep the runaway alive, slowing
  everything down before the cap fires.
- Graceful fallback: if `systemd-run` is unavailable (macOS, CI image, container) `MEM_WRAP=()` empty and the commands
  run unwrapped — no behaviour change. A one-shot warning prints on the macOS / non-systemd path so the user knows the
  cap is inactive.

### macOS compatibility

`systemd-run` is Linux-only. macOS has no clean cgroup analog without root, so on Apple Silicon / Intel Mac the mem cap
silently degrades:

| Component                        | Linux       | macOS                             |
| -------------------------------- | ----------- | --------------------------------- |
| `systemd-run` cgroup hard cap    | ✅ enforced | ❌ unavailable, MEM_WRAP=() empty |
| `PYTEST_WORKERS=1` default       | ✅ applies  | ✅ applies                        |
| IDE basedpyright open-files-only | ✅ applies  | ✅ applies                        |
| QG_MEM_CAP env honored           | yes         | no-op + warning                   |

macOS users: keep parallel QGs to 1-2 slots max until a portable cap lands. To silence the per-run warning:
`export QG_MEM_CAP=0` in `~/.zshrc` / `~/.bashrc`.

### Per-box cap recommendations

| Dev box                             | Total RAM | Reserved (OS + IDE + other apps) | Free for QG | `QG_MEM_CAP`                                   |
| ----------------------------------- | --------- | -------------------------------- | ----------- | ---------------------------------------------- |
| Harsh workstation (Linux, this box) | 96 GB     | ~36 GB (60 GB budgeted for work) | 60 GB       | `15G`                                          |
| Teammate laptop (macOS, M5)         | 24 GB     | ~10 GB (other services)          | 14 GB       | `8G` (advisory only — no enforcement on macOS) |
| Default for everyone                | —         | —                                | —           | `10G`                                          |
| CI runner (large)                   | 32+ GB    | low                              | most        | `0` (disable)                                  |

Put per-user overrides in `~/.bashrc` / `~/.zshrc`:

```bash
export QG_MEM_CAP=15G   # Harsh's workstation
# export QG_MEM_CAP=8G    # macOS teammate (advisory only)
# export QG_MEM_CAP=0     # CI / mem-rich host: disable cap entirely
```

### 2 — `PYTEST_WORKERS=1` default

Previously each QG defaulted to `max(1, cpu_count // 4)` workers (4 on a 16-core box). Eight slots × 4 workers × ~2-4GB
peak = ~64-128 GB. The default is now 1.

Per-repo opt-in: set `PYTEST_WORKERS=N` in the repo's `scripts/quality-gates.sh` **before** the `source base-service.sh`
line if the repo is wall-clock-critical and the dev box has memory headroom.

### 3 — IDE basedpyright scope

The VS Code basedpyright extension defaults to `diagnosticMode: "workspace"` which crawls the entire workspace root.
With 30+ sibling repos mounted as worktrees, this can balloon to tens of GB.

Workspace `.vscode/settings.json` now sets:

```jsonc
{
  "basedpyright.analysis.diagnosticMode": "openFilesOnly",
  "basedpyright.analysis.useLibraryCodeForTypes": false,
  "basedpyright.analysis.exclude": [
    "**/.tabs/**",
    "**/.venv*/**",
    "**/node_modules/**",
    "**/build/**",
    "**/dist/**",
    "**/__pycache__/**",
    "**/.playwright-mcp/**",
  ],
}
```

These are workspace-local (the workspace root is NOT a git repo) — each dev box needs them set independently. The
QG-side basedpyright invocation (`basedpyright $SOURCE_DIR/`) is unaffected — it already passes an explicit source dir
and is per-repo scoped.

## Relaxing the constraints later

Pick the knob that matches the bottleneck observed:

| Symptom                                                 | Relax this                                          | How                                                                                                      |
| ------------------------------------------------------- | --------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| QG dies with exit 137 + "killed" message                | per-call `QG_MEM_CAP`                               | `QG_MEM_CAP=20G bash scripts/quality-gates.sh` (or set in repo's `quality-gates.sh` if recurring)        |
| Disable cap entirely (CI, big-mem host)                 | `QG_MEM_CAP=0`                                      | `QG_MEM_CAP=0 bash scripts/quality-gates.sh`                                                             |
| QG is wall-clock-bottlenecked on slow tests             | `PYTEST_WORKERS` in repo                            | add `PYTEST_WORKERS=4` BEFORE `source .../base-service.sh` line in the repo's `scripts/quality-gates.sh` |
| IDE basedpyright not finding cross-repo type errors     | switch back to workspace mode                       | edit workspace `.vscode/settings.json` → `"basedpyright.analysis.diagnosticMode": "workspace"`           |
| Need parallel QG storms (eg dependency-alignment sweep) | stagger via `flock` (post-cutover -- not yet wired) | add `flock /tmp/qg.lock bash scripts/quality-gates.sh` wrapper in caller                                 |

Order of relaxation when adding capacity (more RAM, fewer simultaneous slots):

1. Bump `PYTEST_WORKERS` to 2-4 in the wall-clock-critical repos first.
2. Bump `QG_MEM_CAP` to 16G or 20G if mem caps start firing under normal load.
3. Disable `MEM_WRAP` entirely (`QG_MEM_CAP=0`) only on hosts where the OOM is architecturally impossible (eg ≥256 GB
   RAM CI runners, or ≤2 concurrent slots).

## OLD/NEW comment pattern in `base-service.sh`

The OOM mitigation lines in `scripts/quality-gates-base/base-service.sh` are intentionally written as **commented OLD +
active NEW** rather than as outright replacements. This makes reverting trivial when the root cause is fixed elsewhere
(e.g. a tighter basedpyright cache, a saner xdist worker policy, or a memory leak repaired upstream).

Pattern:

```bash
# ╔══ [OOM MITIGATION — added 2026-05-15] ═════════════════════════════════╗
# OLD (pre-2026-05-15): ...one-line description + the exact previous code...
#     _DEFAULT_WORKERS=$($PYTHON_CMD -c "..." 2>/dev/null || echo 1)
#     PARGS="-n ${PYTEST_WORKERS:-$_DEFAULT_WORKERS} ..."
# NEW (post-OOM): ...one-line reason for change...
# TO REVERT: comment NEW line below, uncomment OLD pair above.
# SSOT: codex/06-coding-standards/quality-gates-memory-governance.md
# ╚════════════════════════════════════════════════════════════════════════╝
PARGS="-n ${PYTEST_WORKERS:-1} ..."   # NEW
```

Three locations use this pattern:

1. **MEM_WRAP block** (top of file, ~30 lines): the systemd-run wrapper builder
   - macOS warning. To fully revert, delete the block AND remove `"${MEM_WRAP[@]}"` prefix from the three call-sites.
2. **PYTEST_WORKERS default** (`PARGS=` line): NEW = `-n 1`, OLD = `-n cpu//4`.
3. **pytest + basedpyright call-sites**: NEW prepends `"${MEM_WRAP[@]}"`; OLD has no prefix. These are SAFE to leave in
   place during a revert because `MEM_WRAP=()` empty array expands to nothing — but if you delete the MEM_WRAP block at
   the top, you MUST also remove the prefix at the call-sites (otherwise `"${MEM_WRAP[@]}"` is undefined and bash
   errors).

Reviewers: when you find an OOM-mitigation block whose root cause is fixed, swap the commented OLD code back in and
delete the NEW + comment block in one commit. Update this doc's "OLD/NEW pattern" section to remove the relevant entry
from the list above.

## Cross-side guidance

Ikenna's side should run the same three guardrails — the `base-service.sh` change auto-applies to every repo that
sources it (no per-repo propagation needed). The workspace `.vscode/settings.json` is per-dev-box and needs to be set on
every operator's workstation independently.

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
