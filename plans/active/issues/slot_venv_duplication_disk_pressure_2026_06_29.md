---
doc_type: issue
title:
  Per-slot × per-repo venv duplication → chronic disk pressure (root cause of the 2026-06-29 disk-full →
  config-corruption incident)
status: active
asset_group: [cross-cutting]
created: 2026-06-29
author: interactive session (infra/devops, claude-opus-4-8)
source: [disk-full incident 2026-06-29, agent-orchestrator@7c72580]
assigned_vm: NA
---

# Per-slot venv duplication → chronic disk pressure

> **Status: the ACUTE incident is already resolved** (config self-heal shipped, runaway container removed, Docker log
> rotation added — see § Completed remediation). This doc captures the **structural** root cause (venv duplication) + a
> **proposed** resolution that the operator wants independently reviewed before rollout. Nothing in § Proposed
> resolution has been applied. `assigned_vm: NA` (not dispatched — review-gated).

## TL;DR

A full root disk truncated several per-slot `.claude.json` files mid-write, which crash-looped the main orchestrator
agent + the Opus-pinned worker slots. The **acute trigger** was a single orphaned test container whose unbounded JSON
log grew to 12.5 GB. The **structural reason the disk was full enough to tip over** is that each of the 16 fleet slots
maintains its **own physical copy** of a `.venv` in **every** repo it touches — and uv's hardlink dedup is **not
currently active**, so identical third-party wheels are stored N times instead of once.

Proposed fix: make uv's hardlink dedup actually work (persistent shared cache on the same filesystem +
`UV_LINK_MODE=hardlink` + a one-time reinstall). This deduplicates **only** immutable third-party wheels; it leaves
per-slot editable/internal-dep isolation completely intact, and has **zero** effect on prod or CI. Operator wants this
isolation claim double-checked by a second agent before any change.

---

## Incident timeline (2026-06-29)

1. Root disk hit ~100% used.
2. The orchestrator's `_ensure_claude_config_dir` seed path (and claude's own runtime writes) were truncated mid-write →
   0-byte / mid-JSON `.claude.json` for `orch-agent-main` and worker slots 5, 13, 16.
3. claude refused to start on those configs (blocking "Configuration Error" modal) → spawn died at paste time →
   `AutoSpawnLoop` re-spawned into the same poisoned config every tick. Slots 5 (the primary Opus-pinned slot), 13, 16
   were starved; main agent went dark.
4. Operator noticed: main agent's tmux field blank + inactive; "Opus workers won't spin up."

---

## Root cause analysis

### Acute trigger (RESOLVED) — unbounded container log

A leftover manual test container `alerttest4` (`alerting-service:8e511d4`, `RestartPolicy=no`, no compose/systemd owner,
no published ports) had been running 6 days in a credential-failure retry loop **with no backoff**:

```
WARNING alerting_service.subscribers.alert_subscriber subscribe_once(<sub>) failed —
  Your default credentials were not found ...   (repeated several times/ms for 6 days)
```

Docker had **no log rotation** (`/etc/docker/daemon.json` absent → `json-file` driver defaults = **unbounded**), so that
container's `…-json.log` grew to **12.5 GB**. It was the single largest file on the box.

### Structural baseline (THIS issue) — per-slot × per-repo venv duplication

`du` breakdown at incident time:

```
/home/ubuntu/unified-trading-system-repos/.tabs   90 GB   (16 per-slot worktrees)
  .tabs/3  29 GB   .tabs/1  27 GB   .tabs/4  18 GB     ← 74 GB in 3 slots
  .tabs/{2,5..16}  ~0.4–0.5 GB each                    ← slots that haven't materialised many venvs yet
```

Each fat slot is dominated by `.venv` dirs — **one per repo, per slot** (ml-service/.venv 2.6 GB, e2e-testing/.venv 2.5
GB, system-integration-tests/.venv 2.3 GB, …). With ~28 repos × 16 slots, the worst case is enormous; the disk survives
only because most slots haven't yet built every venv.

**uv dedup is NOT active** — proven by inode identity on the heaviest shared file (`nvidia/nccl/lib/libnccl.so.2`, ~412
MB):

```
ml-service/.venv/.../libnccl.so.2          inode 3248993  links=1   412003816 bytes
.tabs/3/ml-service/.venv/.../libnccl.so.2  inode 2936224  links=1   412003816 bytes  ← same bytes, DIFFERENT inode
.tabs/4/ml-service/.venv/.../libnccl.so.2  inode 2172251  links=1   417480400 bytes  ← (also a different version)
```

Three independent inodes, each `links=1` = three full physical copies. If uv were hardlinking from its cache, all three
would share **one** inode (`links ≥ 3`).

**Why dedup isn't working:** the venvs ARE created by uv (`pyvenv.cfg` shows `uv = 0.11.15`), and uv's default link mode
IS hardlink, and everything is on a single filesystem (`/`). But the uv cache (`~/.cache/uv`) is only **1.4 GB** — far
too small to back 74 GB of venvs. It is being **pruned/cleared between installs**, so each install re-materialises a
fresh copy with a new inode instead of hardlinking to a stable cache entry. The cache is the hardlink source; clearing
it defeats the dedup.

---

## Evidence summary

| Fact                                    | Evidence                                                                                                                           |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Acute trigger = container log           | `…/567f06d2…-json.log` = 12.5 GB, mtime live; container `alerttest4`, `RestartPolicy=no`, 6 days, ADC-fail loop                    |
| No Docker log rotation                  | `/etc/docker/daemon.json` absent → `json-file` unbounded                                                                           |
| Structural baseline = venv dup          | `.tabs` 90 GB; slots 1/3/4 = 74 GB; per-repo `.venv` per slot                                                                      |
| uv dedup inactive                       | 3× `libnccl.so.2` with distinct inodes, `links=1`                                                                                  |
| uv is in use                            | `pyvenv.cfg` → `uv = 0.11.15`; `uv 0.10.8` on PATH                                                                                 |
| Cache too small / pruned                | `~/.cache/uv` = 1.4 GB vs 74 GB of venvs                                                                                           |
| Internal deps are editable path sources | consumer `pyproject.toml`: `[tool.uv.sources] path="../X" editable=true` + version contract in `[project.dependencies]`            |
| Per-slot isolation is real              | slot 3 venv → `.tabs/3/unified-trading-library`; slot 4 venv → `.tabs/4/unified-trading-library` (distinct `_editable_impl_*.pth`) |

---

## Completed remediation (already shipped — for context, NOT part of the review)

1. **Config self-heal (durable code fix)** — `agent-orchestrator@7c72580`, gate-green, live via `--reload`.
   `_ensure_claude_config_dir` now validates `.claude.json` and **repairs** an invalid one (restore newest valid backup
   → else reseed) with **atomic** writes (`mkstemp` + `fsync` + `os.replace`); a valid config is left untouched. + 18
   unit tests (`tests/test_tmux_spawn_config_repair.py`). Eliminates the crash-loop class structurally.
2. **Acute disk reclaim** — removed `alerttest4` + pruned its image; `/var/lib/docker` 13 GB → 208 KB,
   `/var/lib/containerd` 7.5 GB → 6.2 MB; **~20 GB reclaimed** (disk 63% → 56%). Confirmed **no other dormant
   containers** (docker 0, containerd `moby` ns 0, no other runtimes).
3. **Docker log rotation (recurrence guard)** — wrote `/etc/docker/daemon.json`
   `{"log-driver":"json-file","log-opts":{"max-size":"50m","max-file":"5"}}`; restarted dockerd clean. Any future
   container is now capped at 250 MB of logs.

---

## Proposed resolution (NOT YET APPLIED — the part to review)

Make uv's hardlink dedup actually work. Three settings + a one-time reinstall:

1. **Persistent, shared cache on `/`** — set `UV_CACHE_DIR=/home/ubuntu/.cache/uv` for every slot (export in the
   slot-spawn environment), and **stop blanket-pruning it**. Bound growth with `uv cache prune` (removes only
   _unreferenced_ entries), never a full clear. The cache is the hardlink source.
2. **Force hardlink mode** — `UV_LINK_MODE=hardlink` (explicit, so it can't silently fall back to copy). Same-filesystem
   requirement is satisfied (all under `/`).
3. **One-time reinstall** — `uv sync --reinstall` (or recreate venvs) per slot so existing _copied_ files re-materialise
   as hardlinks to the stable cache. uv does not retroactively dedupe files already on disk.

After this: each unique `(package, version)` is stored **once** in the cache and every venv hardlinks to it → marginal
disk cost of an Nth slot for shared third-party deps ≈ 0.

### Why this is safe — the dividing line

| Layer                                                                            | Storage                                                                                                                 | Isolation                                                           |
| -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| **Internal / editable deps** (the repo a slot is changing + its path-dep'd libs) | per-venv `_editable_impl_*.pth` finder → _that slot's_ worktree source; a few bytes; **never cached, never hardlinked** | **per-slot, live, fully isolated**                                  |
| **Third-party wheels** (torch, nvidia, pandas…)                                  | shared uv cache + hardlink                                                                                              | deduped — correct, since every slot wants identical immutable bytes |

The thing that must stay isolated (editable internal source) is exactly what uv leaves per-venv. The thing that's safe
to share (immutable versioned wheels) is exactly what it dedupes. The two operate on different artifacts and cannot
collide. Invariant: **"the version you're editing is an editable path source → isolated; the version you're consuming as
a pin is a wheel → shareable."**

### Cross-slot editing — answered

Slot 3 and slot 5 can edit `instruments-service` / UTL **differently and simultaneously** with full isolation. Each slot
is a separate `git clone --reference` worktree; the relative path `[tool.uv.sources] path = "../X"` resolves to _that
slot's own_ `.tabs/N/X`; the editable install links to it live. Consumers in slot 3 import slot 3's changes; consumers
in slot 5 import slot 5's. This already works today and is **unchanged** by the dedup (editable sources are never
cached).

### Prod — unaffected

`[tool.uv.sources]` is a workspace-dev-only override; it is **not** baked into the published wheel and is ignored when
the package is consumed from an index. Prod resolves the **version contract** (e.g.
`unified-trading-library>=0.13.0,<1.0.0`) to a published, versioned wheel shipped inside the container image. Editable
links + the local hardlink cache never reach a prod artifact. Prod correctness is governed by pinned versions + the
lockfile, exactly as today.

### CI — unaffected

CI runs in ephemeral runners with their **own** cache, so the dev host's cache config never touches CI determinism. CI
resolves from `uv.lock` + version constraints; integration uses the dep-branch cascade (quickmerge STAGE 0 cascades the
dep-branch to transitive ancestors) + SIT at the staging boundary. A slot's local editable change is validated by CI
only after commit/push, when the consumer's CI resolves the new published/branch-matched version. The local-disk cache
optimization is invisible to this.

---

## Verification plan (single-slot proof before fleet rollout)

1. Pick one idle slot (e.g. a `~0.5 GB` slot, or temporarily one of 1/3/4).
2. Record `du -sh .tabs/<N>` and global `df -h /`.
3. Export `UV_CACHE_DIR=/home/ubuntu/.cache/uv` + `UV_LINK_MODE=hardlink`; `uv sync --reinstall` that slot's repos.
4. Re-measure; verify (a) disk drop, (b) `libnccl.so.2` now shares an inode with the cache (`stat -c '%i %h'` →
   `links ≥ 2`), (c) the slot's tests still pass (editable isolation intact), (d) a consumer still resolves its internal
   dep to the **same slot's** worktree (re-check the `_editable_impl_*.pth` path).
5. Only if (a)–(d) hold: roll `UV_CACHE_DIR` + `UV_LINK_MODE` into the slot-spawn env (agent-orchestrator `tmux_spawn`
   env exports) + schedule a one-time fleet `uv sync --reinstall`
   - replace any cache-clearing cron with `uv cache prune`.

---

## Questions for the reviewing agent (operator-requested confirmation)

1. **Isolation:** Confirm the dividing-line claim — that hardlink dedup touches **only** cached third-party wheels and
   **never** editable path sources, so two slots editing the same internal repo stay isolated. Any path-dep edge case
   where a hardlinked file could be shared across slots for a repo under active local change?
2. **CI/SIT:** Confirm `[tool.uv.sources]` path overrides do not leak into published wheels and that CI/SIT determinism
   is governed by `uv.lock` + version constraints + the dep-branch cascade, independent of the dev-host cache.
3. **Cache pruning:** Is anything in the fleet currently clearing `~/.cache/uv` (cron, quickmerge, slot-setup)? That's
   the suspected reason dedup is inactive — needs to be found and switched to `uv cache prune`.
4. **Reinstall blast radius:** Is a one-time fleet `uv sync --reinstall` safe to run while slots are live, or must it be
   staged per-idle-slot? (Editable source is untouched; only third-party wheels re-link.)
5. **Structural alternative:** Is per-repo-per-slot venv the right granularity at all, or should the fleet move toward a
   uv workspace / single-venv-per-slot model? (Out of scope for the immediate fix, but worth a position.)

---

## Codex SSOTs

- `codex/05-infrastructure/per-tab-worktrees.md` — per-slot `git clone --reference` worktree model.
- `codex/04-architecture/tier-and-import-architecture.md` — tier/import rules; services integrate by contract + mocks,
  not direct service↔service deps.
- `codex/06-coding-standards/integration-testing-layers.md` — SIT at the staging boundary.
- `codex/08-workflows/ci-cd-flow.md` — dep-branch cascade, quickmerge, LDR/main promotion.
