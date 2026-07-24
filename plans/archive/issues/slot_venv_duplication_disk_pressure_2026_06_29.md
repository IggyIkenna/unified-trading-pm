---
doc_type: issue
title:
  Per-slot × per-repo venv duplication → chronic disk pressure (root cause of the 2026-06-29 disk-full →
  config-corruption incident)
summary:
  A full root disk truncated several per-slot `.claude.json` files mid-write, which crash-looped the main orchestrator
  agent + the Opus-pinned worker slots. The **acute trigger** was a single orphane...
status: resolved # (was: open) 2026-07-17 — C1–C5 shipped+live since 2026-06-29 (links=81 re-proof); recurrence re-verify measured + remediated (guard 2h cadence, prune cron); B2 interactive-shell gap closed cross-host (pm@86dea79d5); stale 30G pre-convention cache deleted (18G freed, measured)
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, alerting-service, e2e-testing, instruments-service, market-tick-data-service, ml-service]
scope: [engineer, admin]
tags: [infrastructure, orchestrator, self-healing, quality-gates, performance, monitoring]
related: []
created: 2026-06-29
parent_epic: infrastructure_master
priority: P2
source: [disk-full incident 2026-06-29, agent-orchestrator@7c72580]
assigned_vm: NA
resolved_by:
  "operator-audited close 2026-07-17 (hk session) — final flips + evidence in
  plans/archive/2026_07/ao_host_disk_pressure_2026_07_16.md; convention codified in
  /codex/05-infrastructure/per-tab-worktrees.md § Shared uv cache"
locked_by: # cleared 2026-07-17 — operator granted [unlock-plan] explicitly (AskUserQuestion ruling, same session as the 30G deletion)
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-17
locked_since: # cleared 2026-07-17 with the [unlock-plan] grant (was 2026-05-21)
---

# Per-slot venv duplication → chronic disk pressure

> **📦 RESOLVED + ARCHIVED 2026-07-17 (operator-audited, `[unlock-plan]` granted).** Everything this doc tracked is
> closed with measured evidence: the C1–C5 hardlink-dedup fix live since 2026-06-29 (re-proven on the real VM,
> links=81); the 2026-07-13 recurrence re-verified + remediated (verdict _guard-running-but-outgrown_ → guard cadence
> `0 */2` + prune cron, executed by `../2026_07/ao_host_disk_pressure_2026_07_16.md`); the B2 interactive-shell gap
> closed cross-host via `scripts/dev/install-uv-cache-shell-env.sh` (`pm@86dea79d5`, planning VM + hk dev host); and the
> stale 30G pre-convention `/active/uv-cache` deleted (18G measured freed — hardlinked venvs unharmed, as predicted).
> Durable convention: `/codex/05-infrastructure/per-tab-worktrees.md` § "Shared uv cache".

> **✅ SHIPPED + ROLLED OUT 2026-06-29** (claude-opus-4-8, interactive): the corrected C1–C4 are LIVE —
> `agent-orchestrator@e168f1a` (tmux_spawn spawn env + vm-disk-guard fix) + `unified-trading-pm@257c1413b`
> (base-service.sh, PR #733), both QG-green at HEAD (PM QG dogfooded the shared cache). Staged idle-slot reinstall
> reclaimed **21 GB** (disk 60%→53%); live/skipped slots dedupe organically on their next QG. Full numbers in §
> Validation results + § Rollout results. The "proposed / reviewed" banners below are kept as the decision record.

> **Status: the ACUTE incident is already resolved** (config self-heal shipped, runaway container removed, Docker log
> rotation added — see § Completed remediation). This doc captures the **structural** root cause (venv duplication) + a
> **proposed** resolution that the operator wants independently reviewed before rollout. Nothing in § Proposed
> resolution has been applied. `assigned_vm: NA` (not dispatched — review-gated).
>
> **🔎 REVIEWED 2026-06-29** (second agent, claude-opus-4-8): approach is **sound and safe to roll out**, isolation
> claim **CONFIRMED**, prod/CI **unaffected** — BUT the original Proposed-resolution has **two defects that would make
> it fail on rollout**: (1) it doesn't identify that **`vm-disk-guard.sh` is the script wiping the cache** and would
> keep undoing the fix every 6h; (2) the hardcoded `UV_CACHE_DIR=/home/ubuntu/.cache/uv` is **cross-filesystem on at
> least one fleet host** → hardlinks silently fall back to copy → dedup never happens. Corrected implementation + the
> regression surface are in **§ Reviewing-agent findings** below. Do NOT roll out the original three-step list verbatim
> — use the corrected version.

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

> **⚠ REVIEW CORRECTION (evidence slightly overstated):** two of these three inodes have **different byte sizes**
> (412003816 vs 417480400) = **different package versions**, which can NEVER dedupe regardless of hardlink mode (uv only
> shares same-`(package, version)`). So the real picture is "**2 copies that could merge + 1 genuinely different
> version**," not "3 redundant copies." The conclusion (dedup is inactive) still holds — the two same-size `links=1`
> entries prove it — but cite it accurately.

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

> **⚠ DO NOT ROLL OUT THIS LIST VERBATIM.** Review found two defects: step 1's "stop blanket-pruning it" cannot be done
> as a config preference — a concrete script (`vm-disk-guard.sh`) is doing the pruning and must be changed; and step 1's
> hardcoded `/home/ubuntu/.cache/uv` is **cross-filesystem on a real host** (breaks hardlinks silently). Step 2's
> "same-filesystem requirement is satisfied (all under `/`)" is **FALSE on at least one host** (see findings). Use the
> **corrected three-step rollout in § Reviewing-agent findings → "Corrected implementation."**

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

## Canonical cache-dir derivation (host-agnostic — the SSOT every layer uses)

**Rule:** `UV_CACHE_DIR = <common-workspace-root>/.uv-cache`, where `<common-workspace-root>` is the directory that
contains the repo clones / `.tabs`. **Derived from the on-disk layout, NEVER a hardcoded `~/.cache` path** (the
cross-filesystem trap from § B2). This makes the cache (a) on the SAME filesystem as every slot's
`.tabs/<N>/<repo>/.venv` so hardlinks work, and (b) SHARED across all slots so a third-party wheel is one physical copy
fleet-wide. Works identically on the orchestrator VM, the dev host (`/active/...`), and contributor laptops because it
reads the path, not the host.

```bash
# repo_root = git toplevel of the repo being built (CWD when QG runs)
case "$repo_root" in
  */.tabs/*) ws_common="${repo_root%%/.tabs/*}" ;;   # slot worktree → strip /.tabs/<N>/<repo>
  *)         ws_common="$(cd "$repo_root/.." && pwd)" ;;  # main clone / flat laptop → parent of repo
esac
export UV_CACHE_DIR="${UV_CACHE_DIR:-$ws_common/.uv-cache}"   # respect a pre-set value (spawn env) so all layers agree
export UV_LINK_MODE="${UV_LINK_MODE:-hardlink}"
```

Verified on this host: `.tabs/3/market-tick-data-service → /home/ubuntu/unified-trading-system-repos` and the main clone
`market-tick-data-service → /home/ubuntu/unified-trading-system-repos` both resolve to the same common root.
`workspace-manifest.json` is NOT a root marker (it lives inside the PM repo), and `WORKSPACE_ROOT` is not exported in
slot shells — so the string-strip layout derivation above is the reliable, host-agnostic mechanism.

## For other hosts (contributor laptops / dev machines) — you get this automatically

**You do NOT hand-configure anything per host.** The fix lives in committed code — `base-service.sh` (every QG-driven
`uv sync`) and `tmux_spawn.py` (locally-spawned slots). On any machine, the moment you pull, each QG run derives
`UV_CACHE_DIR=<your-workspace>/.uv-cache` on _your_ filesystem and hardlinks from it. Same benefit, zero per-host setup
— because the derivation reads the on-disk path, not a hardcoded home dir.

1. **Get it (one pull):**

   ```bash
   git -C unified-trading-pm pull --ff-only && git -C agent-orchestrator pull --ff-only
   ```

2. **It activates on your next QG** — `cd <repo> && bash scripts/quality-gates.sh` builds that repo's `.venv` by
   hardlinking from `<workspace>/.uv-cache`. Nothing to export.

3. **Verify it's live (optional):**

   ```bash
   f=$(find <repo>/.venv -name '*.so' -size +50M | head -1)
   stat -c 'links=%h  %n' "$f"      # links >= 2 → hardlinked to the shared cache (dedup ON)
   ```

4. **Reclaim existing duplicates now (optional):** already-built venvs stay as copies until rebuilt. To collapse them
   immediately instead of waiting for organic rebuilds, from your workspace root:

   ```bash
   export UV_CACHE_DIR="$PWD/.uv-cache" UV_LINK_MODE=hardlink
   for r in */; do [ -d "$r.venv" ] && ( cd "$r" && uv sync --frozen --reinstall ); done
   ```

5. **Same-filesystem sanity:** hardlinks need the cache + venvs on one filesystem; the derivation co-locates them, so
   this holds unless you deliberately split repos across mounts. If a cross-device case ever arises,
   `UV_LINK_MODE=hardlink` makes uv **warn and fall back to copy loudly** — never a silent regression. Quick check:
   `df --output=target . .uv-cache` (both rows should match).

~~Optional: if you run `uv` by hand a lot _outside_ QG, add `export UV_CACHE_DIR="<workspace-root>/.uv-cache"` to your
shell rc. Not needed for the QG path (it sets it itself).~~ **CLOSED 2026-07-17 — no longer a per-person optional**:
`scripts/dev/install-uv-cache-shell-env.sh` (`pm@86dea79d5`) installs the export block idempotently into the operator's
shell rc, same `${VAR:-...}` derivation as base-service.sh. Installed + verified on the planning VM
(`i-0c9b283b31d6b5ca7`: interactive `uv cache dir` → `/home/ubuntu/unified-trading-system-repos/.uv-cache`) and the hk
dev host (→ `/active/unified-trading-system-repos/.uv-cache`, which was the live B2 case — hand-run `uv` had been
writing to `/home/hk/.cache/uv`, cross-filesystem on the 84%-full `/`). Run once per remaining host.

## Verification plan (single-slot proof before fleet rollout)

1. Pick one idle slot (no live `orch-slot-<N>` tmux session) with a materialised venv footprint.
2. Record `du -sh .tabs/<N>` and global `df -h /`.
3. Export `UV_CACHE_DIR=<common-workspace-root>/.uv-cache` + `UV_LINK_MODE=hardlink` (the derivation above — **never the
   hardcoded home path**); `uv sync --reinstall` that slot's repos.
4. Re-measure; verify (a) disk drop, (b) `libnccl.so.2` now shares an inode with the cache (`stat -c '%i %h'` →
   `links ≥ 2`), (c) a SECOND idle slot's reinstall hardlinks to the **same** cache inode (cross-slot dedup proof), (d)
   the slot's tests still pass (editable isolation intact), (e) a consumer still resolves its internal dep to the **same
   slot's** worktree (re-check the `_editable_impl_*.pth` path).
5. Only if (a)–(e) hold: ship the code (C1 vm-disk-guard fix + C2–C4 base-service.sh env + spawn env) via quickmerge,
   then schedule the one-time fleet `uv sync --reinstall` staged per idle slot (C5).

---

## Questions for the reviewing agent (operator-requested confirmation)

> **→ ALL FIVE ANSWERED in § Reviewing-agent findings below** (Q1→A, Q2→A, Q3→B1, Q4→E, Q5→D).

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

## Reviewing-agent findings (2026-06-29, claude-opus-4-8, interactive)

**Verdict:** approach is the right immediate fix — endorse it — but the original Proposed-resolution is **not safe to
roll out verbatim**. The isolation/prod/CI claims are confirmed; the implementation has two defects that would make the
fix silently no-op or get reverted within 6h. Corrected rollout below.

### A. What's RIGHT (confirmed by inspection, not taken on faith)

- **Isolation claim (Q1) — CONFIRMED.** Internal deps are editable path sources (`[tool.uv.sources] … editable = true`
  in instruments-service, MTDS, UTL, …) and the materialised finder file points at the slot's **own** worktree —
  verified: `_editable_impl_unified_trading_api.pth` → `/active/unified-trading-system-repos/unified-trading-api`. These
  `.pth` files are a few bytes, **never cached, never hardlinked**. Hardlink dedup touches only immutable third-party
  wheels. Two slots editing the same internal repo stay fully isolated. The dividing-line invariant holds.
- **Prod (Q2) — UNAFFECTED.** `[tool.uv.sources]` is a dev-only override, not baked into the published wheel; prod
  resolves pinned versions from the index inside the container image. The hardlink cache is a local-disk artifact that
  never reaches a prod build.
- **CI (Q2) — UNAFFECTED.** CI runs on ephemeral runners that resolve from `uv.lock`; the buildspecs already cache
  `/root/.cache/uv` independently (`*/buildspec.aws.yaml`). The dev-host cache config is invisible to CI determinism.

### B. What's WRONG / missing (the rollout blockers)

- **B1 — The cache-wiper is `vm-disk-guard.sh`, and it will revert the fix (answers Q3).**
  `agent-orchestrator/scripts/vm-disk-guard.sh:55` does `rm -rf "${home}/.cache/uv" "${home}/.cache/pip"` whenever disk
  ≥ 80%, installed as a **root cron every 6h + @reboot** (`bootstrap_vm.sh` STEP 7.5, ~line 1247). Because the box runs
  chronically near-full, it nukes the hardlink source on nearly every tick. This is a **self-defeating loop**: disk
  fills → guard wipes cache → next `uv sync` has no hardlink source so it re-downloads **and re-copies** (fresh inodes,
  `links=1`) → disk fills again. This is exactly the inode evidence. "Stop blanket-pruning it" is not a config toggle —
  **this script must be edited**, or the fix is gone within 6h.
- **B2 — Hardcoded `UV_CACHE_DIR=/home/ubuntu/.cache/uv` is cross-filesystem on a real host → hardlinks silently fall
  back to copy.** Hardlinks cannot cross filesystems. Measured on the human-planning/dev host:
  - `/active/unified-trading-system-repos` (venvs live here) → `/dev/nvme0n1p2`
  - `/home/hk/.cache` (uv default + the proposed hardcoded path's fs) → `/dev/nvme0n1p1`

  **Different filesystems.** A home-based cache + a workspace-under-`/active` venv = uv copies, never links — so on this
  host dedup is **already** defeated by the fs boundary even independent of B1. The orchestrator VM only works because
  there `$HOME` and the workspace are both under `/home`. The doc's "same-filesystem requirement is satisfied (all under
  `/`)" is host-specific and false in general. **The cache must sit on the same filesystem as `.tabs`, derived from the
  workspace root — never a hardcoded home path.**

- **B3 — The one real regression surface (local only): hardlink mutation semantics.** A hardlink makes the venv file and
  the cache file **one inode**. In-place writes to site-packages propagate to the cache and every other slot sharing
  that inode. In practice this is rare and acceptable: `uv`/`pip` upgrade-uninstall is safe (unlink + relink a new
  inode, never an in-place edit); `.pyc` bytecode is written as new files in `__pycache__`, not edits of the hardlinked
  `.py`. The genuine (low-probability) vectors are a test that monkey-patches a package **on disk**,
  `pip install --target` over site-packages, or hand-editing a package to debug — with 16 slots sharing inodes those
  become cross-slot contamination. Document it; don't roll out claiming "cannot collide" without this caveat. Second
  sharp edge: concurrent `uv cache prune` vs concurrent `uv sync` across 16 slots — prune only when slots are idle, or
  let the cache size float (post-fix it reclaims ≈0 anyway — see C1).

### C. Corrected implementation (use THIS, not the original three-step list)

1. **C1 — Fix `vm-disk-guard.sh` FIRST (it is the actual bug).** Replace the unconditional `rm -rf "${home}/.cache/uv"`
   with `uv cache prune` (keep the `.cache/pip` clear if desired). Key insight: **once hardlinks are active, wiping the
   cache reclaims ≈0 bytes** — the wheel inodes are shared with live venvs, so removing the cache copy frees nothing for
   any referenced wheel. The cache-nuke is then both useless and harmful. The guard's real workhorse — idle-slot venv
   pruning (lines 74-87) and the clean-stray-worktree reaper — stays unchanged and keeps doing the heavy lifting.
2. **C2 — `UV_CACHE_DIR=<workspace-root>/.uv-cache`** (same filesystem as `.tabs`), **derived**, not a hardcoded home
   path. This is correct on every host (orchestrator VM and dev host alike) because it co-locates the cache with the
   venvs it links to.
3. **C3 — `UV_LINK_MODE=hardlink` explicit** — keep this; it makes any future cross-device mismatch **warn loudly and
   fall back to copy visibly** instead of silently copying, so the B2 class surfaces instead of hiding.
4. **C4 — Export C2+C3 in the QG path, not just the spawn env.** The thing that actually builds the venvs is
   `unified-trading-pm/scripts/quality-gates-base/base-service.sh:334`
   (`UV_PROJECT_ENVIRONMENT=.venv uv sync --frozen`), invoked **non-interactively**. The env vars must reach that shell
   — exporting only in an interactive login/spawn env helps Claude's shell but leaves QG (the actual installer) still
   copying.
5. **C5 — One-time `uv sync --reinstall` staged per IDLE slot** (piggyback on the guard's existing idle detection).
   Editable source is untouched; only third-party wheels re-link. Safe to run while other slots are live.

### D. Structural question (Q5) — position

Endorse hardlink dedup as the immediate fix (highest ROI, lowest risk, preserves per-repo-per-slot isolation). **Do
NOT** move to a single-venv-per-slot / uv-workspace model: these are separate git repos with independently pinned
`uv.lock`s, and QG deliberately installs each via `uv sync --frozen` against that repo's own lock to stay byte-identical
with CI (`base-service.sh:303-334`). Collapsing to one env per slot invites cross-repo version conflicts and breaks the
`--frozen`/CI parity — high regression risk for marginal savings beyond what hardlinks already deliver. Once hardlinks
make the Nth slot's wheel cost ≈0, the per-repo-per-slot granularity stops mattering and the structural question
dissolves on its own.

### E. Reinstall blast radius (Q4)

Safe while slots are live **if staged per idle slot** (C5) — editable source is never touched, only third-party wheels
re-link. A simultaneous fleet-wide `uv sync --reinstall` across all 16 live slots is not advised (it would spike
download + I/O and collide with in-flight QGs); gate it on the same idle check `vm-disk-guard.sh` already uses (no live
`orch-slot-<N>` tmux session).

## Validation results (2026-06-29, implementation + proof)

**Mechanism (clean-room, this host `/`):** two throwaway venvs installing the same `numpy==2.1.0` with `UV_CACHE_DIR` on
the workspace FS + `UV_LINK_MODE=hardlink` → the 30 MB openblas `.so` shows `inode=… links=3` in BOTH venvs (cache +
venvA + venvB). One physical copy.

**Real slots (slots 3 + 4, both idle, ml-service `uv sync --frozen --reinstall` with the derived shared cache):**

```
slot3 libnccl.so.2  BEFORE inode=2936224 links=1   →  AFTER inode=12078862 links=2   (hardlinked to shared cache)
slot4 libnccl.so.2  BEFORE inode=2172251 links=1   →  AFTER inode=12078862 links=3   ← SAME inode as slot3
disk / : 177G→173G used  (4 GB reclaimed from just 2 slots' ONE repo)   shared cache = 7 GB (one copy of everything)
slot3 editable pointer → .tabs/3/ml-service   (per-slot isolation INTACT)
smoke import: python 3.13.13, numpy 2.3.5 OK  (reinstalled venv works)
```

Confirms: cross-slot hardlink dedup works on real venvs, real disk is reclaimed, per-slot editable isolation is
preserved, and the venv still imports. Extrapolated fleet reclaim is large (slots 1/3/4 alone were 74 GB of mostly
third-party wheels that collapse to one shared copy).

**Bonus finding — `--frozen` reinstall also heals lock-drift.** slot 4's pre-existing `libnccl.so.2` was a DIFFERENT
build (417480400 bytes) than slot 3's (412003816); after the `--frozen` reinstall both are the locked 412003816 build
and share an inode. So the migration reinstall not only dedupes but corrects venvs that had drifted from their committed
`uv.lock` — a latent local↔CI parity gap on any slot whose venv was last built against an older lock.

**Shipped implementation (the corrected C1–C4):**

- `unified-trading-pm/scripts/quality-gates-base/base-service.sh` — derive common workspace root (string-strip
  `/.tabs/`, else parent-of-repo) → export `UV_CACHE_DIR=<root>/.uv-cache` + `UV_LINK_MODE=hardlink`, inside the no-CI
  guard so CI buildspecs (own `/root/.cache/uv`) are untouched. Respects a pre-set `UV_CACHE_DIR`.
- `agent-orchestrator/scripts/vm-disk-guard.sh` — removed the `rm -rf …/.cache/uv` nuke of the active cache (kept the
  legacy home-cache + pip/npm clears); added a `uv cache prune` (per workspace, as owner) for bounded growth.
- `agent-orchestrator/server/tmux_spawn.py` — slot spawn env exports the same derived `UV_CACHE_DIR` + `UV_LINK_MODE` so
  interactive `uv` runs dedupe like QG does.

## Rollout results (2026-06-29, staged per-idle-slot reinstall)

Migrated the legacy `~/.cache/uv` → `<workspace>/.uv-cache` (same-FS rename, warms the cache), then ran a staged
`uv sync --frozen --reinstall` over IDLE slots (re-checking liveness per slot and per repo).

```
slots 1,2,3      LIVE — skipped (never touched)
slot 4           went LIVE mid-pass → ABORTED after 2 venvs (per-repo liveness re-check fired)
slots 5,7,8,10   reinstalled 3/1/5/6 venvs → deduped
slots 6,9,11-16  0 materialised venvs (nothing to dedupe yet)
disk /: 174G→153G used (60%→53%)   NET RECLAIMED: 21 GB   shared cache 7→8 GB (union of all wheels)
```

Post-rollout verification: cross-slot dedup confirmed (slots 3+4 `libnccl.so.2` share inode 12078862, `links=3`); a
reinstalled idle slot's venv still imports (slot 8 e2e-testing, py 3.13.13); per-slot editable isolation intact (slot 5
UTL → `.tabs/5/...`, slot 8 UTL → `.tabs/8/...`).

**Live + skipped slots need no manual action** — base-service.sh now sets the shared cache on every QG run, so slots
1/2/3/4 (and the main clones, deliberately skipped) dedupe **organically** on their next QG. The idle-gating proved
safe: live slots were never touched and a slot that went live mid-pass was abandoned cleanly. Disk journey this
incident: ~100% (full → config corruption) → 56% (after container cleanup) → **53% used / 138 GB free**, with the fix
self-sustaining (vm-disk-guard no longer nukes the cache).

## Codex SSOTs

- `/codex/05-infrastructure/per-tab-worktrees.md` — per-slot `git clone --reference` worktree model.
- `/codex/04-architecture/tier-and-import-architecture.md` — tier/import rules; services integrate by contract + mocks,
  not direct service↔service deps.
- `/codex/06-coding-standards/integration-testing-layers.md` — SIT at the staging boundary.
- `/codex/08-workflows/ci-cd-flow.md` — dep-branch cascade, quickmerge, LDR/main promotion.

### 2026-07-13 — slot 7: disk pressure recurred/escalated past the 2026-06-29 post-fix baseline

Hit this same class of pressure again while shipping an unrelated dependency-alignment fix
(`dependency_alignment_red_multi_repo_ceiling_drift-002`). `df -h /home` momentarily read **2.0MB free on the 290G root
disk (100% used)** mid-QG-run for `strategy-service`, causing a real, confirmed collateral failure: pytest's tmp-dir
fixture setup failed fleet-wide across the run with `OSError: could not create numbered dir ... after 10 tries` under
`/home/ubuntu/.cache/ qg-tmp/pytest-of-ubuntu/...` — a disk-exhaustion artifact, not a code regression (verified: the
actual dependency fix — `pillow>=12.3.0` — was independently confirmed correct via an identical, already-fully-green
sibling fix in `execution-service`, a fresh `check-dependency-alignment.py` pass, and a direct `import PIL` sanity
check). Disk fluctuated (2MB → 12-13G free → 96-97% used) within minutes, consistent with many concurrent slots'
QG/uv/pytest churn rather than one runaway process — did not independently re-diagnose (this doc's own C1-C5 fix +
`vm-disk-guard.sh` are already the owning mechanism; re-investigating from scratch would duplicate effort). Not filing a
new issue doc — this is the same structural class already tracked here, now past its post-fix 53%-used baseline again.
Whoever next works this doc's remaining open surface (if any) should re-verify `vm-disk-guard.sh`'s idle-slot
reinstall + `uv cache prune` are still running as scheduled, and check whether the fleet has simply grown (more live
slots × more materialised venvs) past what the 2026-06-29 hardlink-dedup fix alone can absorb.

## Open follow-up

> Formalised 2026-07-16 during the AO issue-doc audit: the 2026-07-13 recurrence above was narrative-only with **no
> checkbox**, so it was invisible to every tracking sweep — exactly the "untracked follow-up" class. The structural
> C1–C5 fix is code-verified still live (shared `UV_CACHE_DIR` + `UV_LINK_MODE=hardlink` exported by
> `quality-gates-base/base-service.sh` and `tmux_spawn.py`; `vm-disk-guard.sh` no longer nukes the active shared cache)
> — so this is a **re-verification**, not a re-fix.

- [x] [INFRA] P2. ✅ **DONE — measured live on the real orchestrator VM (`i-0c9b283b31d6b5ca7`) via read-only AWS SSM,
      2026-07-16 + re-measured 2026-07-17. Verdict: _guard-running-but-outgrown_, now remediated.** (1) **Dedup holds**
      — shared `_duckdb…so` at inode 4620498 with **links=81**; largest slot 18G vs the pre-fix 27–29G outliers, so
      fleet growth has NOT outpaced hardlink-dedup. (2) **Guard runs on schedule and works every cycle** — 7 firings/3
      days, each reclaiming 15–30 points (`95%→76%`, `86%→61%`, `85%→65%`, …). (3) The residual gap was **growth rate
      between firings** (max +19 points/6h → a 79% "nothing to do" reading flew blind to 85%): remediated by
      `ao_host_disk_pressure_2026_07_16` — guard cadence `0 */6` → `0 */2` plus the `install-prune-uv-cache-cron.sh`
      install (it had never actually been installed; also fixed its cron-PATH bug, `pm@88310f87a`). Post-remediation
      proof 2026-07-17T14:00Z: guard read **83% → vacuumed → 51%** within the same firing; disk at 58% with 124G free.
      Closed together with the `ao_docs_reconciliation_2026_07_15.md` disk/venv row (annotated there — no double-book).
      Provenance: this doc's 2026-07-13 entry; execution + evidence in
      `../../archive/2026_07/ao_host_disk_pressure_2026_07_16.md`.
- [x] [INFRA] P3. ✅ **DONE 2026-07-17 — operator reversed the same-day "keep for now" to "delete it now" and it is
      GONE, with the hardlink prediction confirmed by measurement.** `rm -rf /active/uv-cache` executed (contents as
      `hk`; the empty root-owned-parent husk needed one `sudo rmdir`): `/active` free space **104G → 122G = 18G actually
      freed** of the 30G `du` size — the ~12G delta is exactly the hardlinked blobs (links≥2) whose venv-side copies
      survive, i.e. the "real reclaim < 30G, venvs unharmed" call made when this was parked. Path verified absent
      post-delete. (History: FORMER pre-convention cache, dead since 2026-07-08, zero references; migrated here from
      `ao_host_disk_pressure_2026_07_16`'s Deferred table on its archival earlier the same day.) **Gate MET**: measured
      freed GB recorded; nothing references the path.
