---
doc_type: issue
title: Host root disk hit 100% full (0 bytes free) TWICE in one session — recurring, not transient
summary: |
  While running quality-gates.sh for unified-trading-api, the shared host's root filesystem (290G, holds
  /home/ubuntu/unified-trading-system-repos across all 16 slots) hit 100% full — 0 bytes available, breaking `uv sync`
  (`No space left on device`) and the Claude Code harness's own tmpdir output capture. Self-recovered to 96% (13G free)
  ~2 minutes later, unattended. Recurred ~1 hour later, same session, same host — `df -h /` back to 100%/12M free,
  breaking `bash scripts/setup.sh` for execution-service (`uv pip install -e .` editable-install failure). Two
  independent full-disk events in one session upgrades this from "self-recovered blip" to "recurring capacity
  problem" — retitled + reprioritized accordingly.
status: open
nature: process
asset_group: [infrastructure] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, disk-space, host-contention, capacity, recurring]
created: "2026-07-13"
author: unknown
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
archive_exempt: true # 2026-08-09: 0 open todos, full archival deferred -- see Progress Log 2026-08-09
context_scope:
  [
    /plans/archive/issues/qg_host_governor_severe_contention_2026_07_13.md,
    scripts/dev/prune-uv-cache.sh,
    scripts/dev/install-prune-uv-cache-cron.sh,
  ]
source: [unified_trading_api_pip_audit_stale_ignore_list-001 -- observed while shipping the dependency fix]
related:
  [
    /plans/archive/issues/qg_host_governor_severe_contention_2026_07_13.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/issues/tabs_mount_boundary_defeats_uv_cache_hardlink_dedup_2026_08_09.md,
    /plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md,
    /plans/active/issues/host_tmp_tmpfs_full_breaks_pytest_write_2026_08_09.md,
  ]
depends_on: []
---

# Host root disk hit 100% full TWICE in one session — recurring, not transient

## Recurrence (2026-07-13, ~1hr after first occurrence)

`df -h /` again showed `290G 290G 12M 100% /` while trying `bash scripts/setup.sh` for execution-service (to run its
health-endpoint tests as part of `utl_reuse_phase6_venue_health_retry` VERIFY work). `uv pip install -e .` failed at
"Project editable install failed". Same host, same session, same symptom class as the first occurrence below — this is
NOT a one-off. Between the two events, disk was observed oscillating in the 96%-99% range (checked repeatedly while
separately waiting on `qg-host-governor` queue timers), so the host appears to be running close to full most of the
time, with occasional excursions to literal 100%/0-bytes-free rather than a single anomalous spike.

## What I found (first occurrence)

`df -h /` went from ~93M free to **0 bytes free (100%)** between two checks a few minutes apart, while shipping a
routine dependency fix for `unified-trading-api`. Concrete breakage observed during the window:

- `uv sync` failed installing `nodejs_wheel_binaries`: `No space left on device (os error 28)` copying into `.venv`.
- The Claude Code harness's own output-capture tmpdir (`/home/ubuntu/.claude-configs/.../tasks`) also lives on the same
  full root filesystem — simple commands (`df -h`, `kill`) started failing with "Command output was lost ... 0MB free"
  until I redirected `CLAUDE_CODE_TMPDIR` to `/tmp` (a separate, mostly-empty tmpfs mount: `/tmp` was 64% used of 2.0G
  at the same moment `/` was 100% of 290G — `/dev/shm` had 31G entirely free too).
- `/home/ubuntu/unified-trading-system-repos/` alone is ~219G of the 290G root filesystem (16 slots × ~24 repo clones
  each, each with its own `.venv` + `.git` + shared `.uv-cache`).
- Self-recovered to 96% (13G free) roughly 2 minutes later with no action from me — consistent with a concurrent process
  (another slot's QG run, a cache prune, a build cleanup) freeing space, not a fix I applied.

## Why it matters

Same class of problem as `qg_host_governor_severe_contention_2026_07_13.md` (16+ slots all running heavy builds/tests
concurrently on shared host resources) but for **disk** instead of CPU/token concurrency — and disk-full is worse than a
slow queue: it causes hard failures (`uv sync`, coverage.xml writes, git operations) rather than just latency, and it
can transiently break the harness's own tooling (output capture), which is confusing to debug from inside an agent
session (looks like a tool bug, not a resource exhaustion symptom, until you check `df -h`).

## Recommended decision

Worth someone with host-capacity context checking: (1) whether the `.uv-cache` at
`/home/ubuntu/unified-trading-system-repos/.uv-cache` is being pruned on any schedule (a shared cache across 16 slots
can grow unbounded if not), (2) whether per-slot `.venv` dirs could be more aggressively cleaned between tasks, (3)
whether a disk-usage alert/threshold should exist alongside the QG-governor's memory-pressure awareness. **Upgraded to
P1** after the recurrence — a host oscillating between 96-100% full for an extended period (not a single anomalous
spike) means any of the 16 slots can hit this at any moment, and it silently blocks routine work (`uv sync`,
`scripts/setup.sh`, coverage writes) with a confusing error surface (looks like a dependency/tooling bug until `df -h`
is checked). Two independent host-capacity symptoms (CPU/token queue contention + disk-full) surfacing repeatedly in one
session on one host is worth someone connecting the dots on overall host sizing vs current fleet size (16 slots × ~24
repo clones each appears to be the actual driver, per the ~219G `unified-trading-system-repos` footprint noted above).

## Todos

- [x] ✅ [INFRA] P1. Check whether `.uv-cache` / per-slot `.venv` growth is unbounded and needs a prune schedule;
      connect to the QG-governor contention finding for an overall host-capacity review. Given the recurrence, also
      consider whether a per-slot disk-usage cap or an automated `.venv`/cache prune cron is warranted, not just a
      one-time cleanup. (repo: infra/host config) — **INVESTIGATED + PARTIALLY FIXED, slot 11, 2026-07-13**:
      `unified-trading-pm@9dcd37631`. - **Confirmed root driver #1 (shared, safe to fix)**: `.uv-cache` (12G) had NO
      prune schedule at all (no crontab entry, no systemd timer). A single manual `uv cache prune` (no `--force` —
      respects in-use checks) reclaimed **5.7GiB in ~3s**. Shipped `scripts/dev/prune-uv-cache.sh` + idempotent per-host
      installer `scripts/dev/install-prune-uv-cache-cron.sh` (6h default cadence), mirroring the existing
      `cleanup-stale-qg-tmp.sh` convention exactly. **NOT yet actually scheduled** — could not self-install from this
      sandboxed slot session (`crontab -l`/`-e` both hit `Permission denied` for this user on this host); an operator or
      a root-capable agent needs to run `bash unified-trading-pm/scripts/dev/install-prune-uv-cache-cron.sh` once. -
      **Confirmed root driver #2 (larger, NOT fixed — live data)**: per-slot `.venv` dirs are the dominant consumer,
      ~150-200G summed across the 16 slots (1.3-2.6G per heavy repo × ~5-6 heavy repos × 16 slots).
      `UV_LINK_MODE=hardlink` IS configured (`base-service.sh:322`) but is NOT actually deduping across slots — verified
      by comparing the same `numpy.libs/libscipy_openblas64_*.so` file across two different slots' `.venv`s: identical
      content/size, but `nlink=1` on both with DIFFERENT inodes (not hardlinked to each other). Root cause of the
      non-dedup not investigated further this dispatch (candidate: each slot's `uv sync` may resolve to a distinct cache
      entry, or hardlink only applies within a single sync's own cache→venv copy, not across independently-run syncs).
      Did NOT touch any slot's `.venv` — these are live, in-use directories; a blanket prune risks breaking an active
      slot's `quality-gates.sh`/`quickmerge.sh` mid-run (same "never overwrite live foreign WIP without a liveness
      check" principle as `features_sports_parallel_backfill_vm_name_collision_2026_07_13.md`'s VM-name-collision
      fix). - **Follow-on todos** (not done this dispatch, out of single-worker scope): (a) operator runs the cron
      installer above; (b) investigate why `UV_LINK_MODE=hardlink` isn't deduping across slots — if fixable, the
      150-200G `.venv` footprint could shrink dramatically for free; (c) if hardlink-dedup can't be made to work
      cross-slot, a liveness-aware per-slot `.venv` prune (idle-slot detection, same pattern as the VM-collision guard)
      is the real fix for driver #2, not a blanket cron.
- [x] ✅ [INFRA] P2. **CORRECTED VERDICT, 2026-08-09**
      (`tabs_mount_boundary_defeats_uv_cache_hardlink_dedup_2026_08_09.md`, `unified-trading-pm@2c028dee9d`) — the
      leading candidate this todo previously recorded ("`setup.sh` never exports `UV_LINK_MODE`/`UV_CACHE_DIR` itself")
      was NOT the actual root cause and was never applied (`setup.sh` still does not export those vars today). The REAL
      root cause: `UV_CACHE_DIR` was derived as `${WORKSPACE_ROOT}/.uv-cache` — a SIBLING of `.tabs/`, not inside it.
      This host presents `.tabs/` as its own mount/bind boundary; a raw `ln` probe (same methodology as the sibling
      pnpm-store investigation, `ci_satellite_ao_dispatch_batch6_2026_08_08.md` item 10) confirmed `link()` returns
      `EXDEV` for ANY path outside `.tabs/` linking into it, even though `stat -c %d` reports an identical device id on
      both sides — `uv`'s hardlink step was silently falling back to a full copy every time, regardless of
      `UV_LINK_MODE=hardlink` being correctly set. **Fix shipped**: relocated `UV_CACHE_DIR` to
      `${WORKSPACE_ROOT}/.tabs/.uv-cache` (inside the mount boundary) in `scripts/quality-gates-base/base-service.sh`,
      `scripts/dev/install-uv-cache-shell-env.sh`, `scripts/dev/prune-uv-cache.sh`, and
      `scripts/dev/install-prune-uv-cache-cron.sh`; also fixed the identical bug in
      `agent-orchestrator/server/tmux_spawn.py` (AO spawn-time export — same sibling-of-`.tabs` derivation, adjacent
      same-root-cause fix, not scope-limited to this repo since it feeds every AO-spawned worker session). **Verified
      END-TO-END, not just env-vars**: (1) raw `ln` probe from `.tabs/.uv-cache` into a live slot dir succeeds
      (identical inode); (2) a real `uv sync` of `unified-api-contracts` against the relocated cache shows **10/10
      sampled `.so` files at `nlink=2`** (was `nlink=1` fleet-wide, 1,800/1,800, per the 2026-08-08 investigation below)
      — cache→venv hardlink dedup is genuinely restored, not just configured. **(c) the liveness-aware `.venv` prune
      fallback is now MOOT** — the mount-boundary fix alone restores dedup; no fallback needed. (a) unchanged, still
      done 2026-08-07 (see below).

## Progress Log

- **2026-08-09 (infra, `tabs_mount_boundary_defeats_uv_cache_hardlink_dedup-952b1ea6a09b`).** Closed out this doc's sole
  remaining `[INFRA] P2` todo — corrected verdict + shipped fix in-place above (real root cause was the `.tabs/` mount
  boundary, not `setup.sh` env-var propagation; fix relocated `UV_CACHE_DIR` inside `.tabs/` across `base-service.sh`,
  `install-uv-cache-shell-env.sh`, `prune-uv-cache.sh`, `install-prune-uv-cache-cron.sh`, and the adjacent same-bug
  `agent-orchestrator/server/tmux_spawn.py`; verified via a real `uv sync` showing `nlink=2`). Full detail + evidence:
  `/plans/archive/2026_08/issues/tabs_mount_boundary_defeats_uv_cache_hardlink_dedup_2026_08_09.md`. Codex SSOT updated:
  `/codex/05-infrastructure/per-tab-worktrees.md` § "Shared uv cache". **Both todos now `[x]`, `locked_by` empty — this
  doc is archival-eligible; leaving the actual archive-and-referrer-sweep (13 corpus referrers, several archived-doc
  historical mentions) to the next `/ag-closeout-audit infra` or `/na-eligibility-audit` pass rather than absorbing it
  into this narrowly-scoped fix task.**
- **infra_satellite_ao_dispatch_batch6_finalize_2026_08_02.md@infra_satellite_ao_dispatch_batch6_finalize-002,
  2026-08-08**: reconciled this doc's `[INFRA] P2` todo against
  `infra_satellite_ao_dispatch_batch6_2026_08_02.md@88668b743`'s hardlink-dedup investigation (verdict: FIXABLE, not yet
  fixed — concrete leading-candidate fix identified but not built, per batch6's explicit read-only-investigation scope
  exclusion on building/deploying prune tooling). Per the finalize plan's own reconciliation instruction: checkbox left
  OPEN (a concrete fix was identified, just not yet built) and its text narrowed to the remaining fix-build step only
  (add `UV_LINK_MODE`/`UV_CACHE_DIR` exports to `scripts/setup.sh` + single-repo `nlink>1` verification), dropping the
  now-done (a)/(b) framing. Confirmed the cron-install sub-item (a) is correctly `[OPERATOR]`-gated (it was, and is
  already done) and that no `[OPERATOR]` tag is needed on the new narrowed fix-build scope (a repo-local script edit, no
  cron/host permission required). Doc keeps its own operator-gated-by- history remainder — `assigned_vm: NA` unchanged,
  NOT an archival candidate this round (confirms the finalize plan's own stated expectation).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid. The sole open todo (2, bundling
  sub-items a/b/c) is unchanged in count (`grep -cE '^- \[ \]'` = 1) but its content moved substantially today: (a) DONE
  (operator ran the cron installer 2026-08-07); (b) INVESTIGATED today by
  `infra_satellite_ao_dispatch_batch6_2026_08_02.md`'s own `[INFRA] P3` todo (also `[x]` DONE today, cross-referenced
  back to this doc) — root cause confirmed (fleet-wide zero cache→venv hardlink dedup, `scripts/setup.sh` never
  exporting `UV_LINK_MODE`/`UV_CACHE_DIR` itself is the leading candidate) but the investigating agent's own text
  explicitly declines to treat the fix as ready-to-dispatch as-is: "the exact regression trigger needs a live-tracing
  follow-up (out of this read-only investigation's scope)... Recommended next step (not this task's to do — a separate,
  properly-scoped follow-up)." That self-assessment from the same-day investigating worker is a stronger signal than a
  generic "looks bounded" read — a worker already closest to the problem judged it not yet dispatchable without further
  scoping. (c) remains an explicit fallback contingent on (b)'s live-tracing outcome. Net: this doc's own literal
  remaining todo (c, the liveness-aware prune) is still genuinely gated on a not-yet-done follow-up investigation, so it
  does not clear the bounded/deterministic bar today — but the concrete 2-step fix now on record (add
  `UV_LINK_MODE=hardlink`/`UV_CACHE_DIR` exports directly to `scripts/setup.sh`, verify via an `nlink>1` check on one
  repo) is a strong RECLASSIFY-candidate for a fresh, properly-scoped dispatch once that live-tracing step lands —
  flagging, not actioned this run (consistent with this doc's own established practice, e.g. the 2026-08-07 marker's
  identical "flagging as a RECLASSIFY-candidate... not actioned this run"). `assigned_vm: NA` correct.
- **2026-08-08 (infra, `infra_satellite_ao_dispatch_batch6-001`, root-cause investigation of sub-item (b)).** **Root
  cause: CONFIRMED REGRESSION to zero cache→venv hardlink dedup, fleet-wide — not a cache-keying mismatch, not a
  cross-filesystem fallback.** Read-only investigation, no `.venv` modified anywhere, no fresh installs triggered.
  - **Reproduced + extended the 2026-07-13 finding.** Compared the identical `numpy==2.3.5`
    `libscipy_openblas64_-fdde5778.so` (confirmed via `uv.lock`: every checked slot pins the same version, so this is
    NOT a "different package version" false-dedup case) across `deployment-service/.venv` in 7 live slots (2, 4, 6, 8,
    11, 12, 13): **7 distinct inodes, all `nlink=1`, identical size (25,034,001 bytes), identical device (`dev=66305`)**
    — same conclusion as 2026-07-13, same repro, 6 more months of drift later.
  - **The shared cache's OWN copy of that exact file is also `nlink=1`.** Located the single canonical cache entry
    (`~/.uv-cache/archive-v0/7PtdCUWLMi3pew-lyMqNz/numpy.libs/...`, mtime 2026-07-27 — i.e. it existed **11 days
    before** any of the 7 venv copies were built on 2026-08-07). If cache→venv hardlinking worked, every one of those 7
    post-dating installs should have linked to this pre-existing entry (`nlink` climbing to 8). None did. This **refutes
    candidate cause 1** from the original todo ("each slot's `uv sync` may resolve to a distinct cache entry") — there
    is exactly ONE cache entry, confirmed shared, and every slot's lockfile resolves to it.
  - **Fleet-wide sample, not repo-specific:** sampled 1,800 large (`>1MB`) `.so` files across ALL 16 slots'
    `.tabs/*/*/.venv` trees — **1,800/1,800 show `nlink=1`.** Zero cache→venv hardlinks exist anywhere on this host
    right now. This refines **candidate cause 2** ("hardlink may only apply within a single sync's own cache→venv copy,
    not across independently-run syncs") — it is not merely "doesn't survive across syncs," the cache→venv link step
    appears to never fire, even for the very first install that would populate a cold cache entry.
  - **Hardlinking capability itself is NOT broken at the OS/filesystem level.** Root `/` is `ext4` (no reflink/clone
    support, so `hardlink` vs `copy` is the only real choice), and a parallel sample of 152 large files INSIDE
    `.uv-cache/archive-v0` (cache-internal, not cache→venv) found 4 with `nlink>1` (3×`nlink=2`, 1×`nlink=3`) — uv's own
    internal cache-population dedup (identical file content shared between different cache archive entries) demonstrably
    still works. The break is specifically at the **install-into-venv** step, not hardlinking in general.
  - **This is a genuine regression, not "never worked."** The 2026-06-29 fix
    (`/plans/archive/issues/slot_venv_duplication_disk_pressure_2026_06_29.md`) was independently re-proven live on
    2026-07-17 (`links=81` on a shared file) — cross-slot dedup DID work at that point. The fix's code is still present
    and unreverted today: `agent-orchestrator/server/tmux_spawn.py:760` still exports
    `UV_CACHE_DIR=<shared-path>; UV_LINK_MODE=hardlink` into every spawned session; `base-service.sh` still exports the
    same pair (with the correct `.tabs`-relative derivation, not a hardcoded `~/.cache` path); `vm-disk-guard.sh:77`
    still uses the safe `uv cache prune` (not the original `rm -rf` bug). None of the previously-identified failure
    modes (B1/B2 from the archived doc) are back. My own current interactive shell already inherits
    `UV_CACHE_DIR`/`UV_LINK_MODE=hardlink` correctly (verified via `env`), consistent with the fix being intact at that
    layer.
  - **Leading candidate for the regression (not conclusively proven — see verdict):** `scripts/setup.sh` — the script
    that actually builds/refreshes a repo's `.venv` via `uv sync` / `uv pip install -e .` — does **not** itself export
    `UV_LINK_MODE`/`UV_CACHE_DIR` anywhere; it relies entirely on inheriting them from its caller's environment. This
    makes venv-building fragile to ANY invocation path that doesn't already carry the vars — grepped
    `agent-orchestrator/server/*.py` for a `subprocess`-driven `setup.sh`/`uv sync` call that might run with a
    scrubbed/minimal env (none found conclusively; `autospawn.py` only mentions `uv sync` in a comment). The
    2026-08-07-dated venvs sampled above were NOT limited to the 5 repos affected by the 2026-08-05T11:24:53Z
    security-driven git-history rewrite
    (`issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`) — `deployment-service` and
    `market-tick-data-service` are unaffected by that rewrite — so a mass-reclone provisioning gap is a plausible
    contributing factor for the history-rewrite-affected repos specifically, but does NOT by itself explain the fully
    general, 1,800/1,800 fleet-wide failure rate observed above.
  - **Verdict: FIXABLE, not yet fixed.** The mechanism is proven to work end-to-end when the environment correctly
    reaches the actual `uv` install invocation (2026-07-17 proof). The current 100% fleet-wide failure means something
    in the actual install call path is not receiving/honoring `UV_LINK_MODE=hardlink` — most likely an
    environment-propagation gap somewhere between session spawn and `setup.sh`'s `uv sync` call, though this read-only
    investigation could not conclusively isolate the exact break point (that would require a live, monitored `uv sync`
    re-run — e.g. `UV_VERBOSE=1`/strace on a real install — which is explicitly out of this task's read-only scope).
    **Recommended next step** (not this task's to do — a separate, properly-scoped follow-up): (1) add an explicit
    `export UV_CACHE_DIR=...; export UV_LINK_MODE=hardlink` directly inside `setup.sh` itself (removing the dependency
    on env inheritance entirely — the same derivation `base-service.sh` already uses), (2) re-run `setup.sh` for one
    repo in one slot and verify `nlink>1` on a shared file immediately after, before rolling fleet-wide. If that alone
    doesn't restore dedup, sub-item (c)'s liveness-aware prune becomes the fallback path.

- **na-eligibility-audit 2026-08-07 (infra tranche)**: KEEP-NA, valid — unchanged since 2026-08-06 (the operator ran the
  cron installer 2026-08-07, closing sub-item (a) inline in the same open checkbox, evidence already cited there).
  Remaining sub-items (b)/(c) — investigate why `UV_LINK_MODE=hardlink` isn't deduping `.venv` across slots, and build a
  liveness-aware per-slot prune if it can't — are bounded investigations, no longer permission-gated now that (a) is
  done, but bundled into the same single checkbox as (a) rather than split out; per the standing note carried since
  2026-08-02, splitting would be editorial authoring outside this skill's apply set. Flagging as a RECLASSIFY-candidate
  worth a fresh look now that the blocking sub-item is closed (not actioned this run).
- **na-eligibility-audit 2026-08-06 (infra tranche)**: KEEP-NA, valid — primary incident resolved; sole follow-on
  (uv-cache prune cron + cross-slot .venv dedup) is operator-scheduling/design work.

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Sole todo's first
  sub-action is explicitly operator-gated (cron install blocked on sandboxed-slot permissions, confirmed via a prior
  session's own Permission denied result).
- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **KEEP-NA, valid — unchanged from the 2026-07-30
  verdict.** In scope this run because the 2026-08-02 corpus-sweep retagged `asset_group: [meta] → [infrastructure]`.
  Read end-to-end; `grep -cE '^- \[ \]'` = **1**, matching this verdict's item count. Unchanged reasoning: the sole todo
  BUNDLES an operator-permission-gated sub-item (a) — installing the uv-cache-prune cron, confirmed blocked by a prior
  session hitting `Permission denied` on `crontab -l`/`-e`, an OS-level permission no cloud identity can self-serve —
  with two investigation sub-items (b)/(c) that are NOT permission-gated. The 2026-08-02 `/ag-closeout-audit infra` run
  reached the same split and called the investigation half "conflict-checked clear". The bundling is the whole blocker:
  flipping the doc exposes (a) to blind dispatch. Splitting one todo into two is editorial authoring, outside this
  skill's apply set (and would grow the NA todo count against the ratchet) — recorded instead as a targeted-extraction
  candidate for a future infra batch.
- **context-scout 2026-08-03**: refreshed context_scope (3 entries, unchanged — verified all still resolve).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (3 entries), unchanged.
- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).
