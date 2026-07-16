---
doc_type: issue
title:
  Orchestrator host /tmp (2GB tmpfs) fills to 100% and makes plan-hygiene / QG hooks fail with SPURIOUS "missing
  required frontmatter field" errors on valid files — fleet-wide commit blocker
summary: >
  On the central orchestrator host (planning VM, slot fleet), `/tmp` is a 2.0GB tmpfs. It reached 100% full (2026-07-16
  ~01:28 UTC) from accumulated, un-reaped agent/QG scratch — notably an 806MB `/tmp/ao-debug-pull-*` directory (18h
  old), two 425MB anonymous temp dirs (34h old), and ~117MB one-off analysis parquets. With `/tmp` full, the pre-commit
  `plan-hygiene` hook's `check_frontmatter` step (which shells out to `awk`) failed with `awk: ... error writing
  standard output: No space left on device`, and — because awk could not write — reported BOGUS `missing required field:
  {parent_epic,title,priority,status,estimate_class,...}` violations against a plan whose frontmatter was in fact
  completely valid. This silently blocks EVERY slot's commits on this host and, worse, is a trap: an agent that does not
  diagnose the `/tmp`-full root cause could waste time "fixing" already-correct frontmatter, get stuck, or (with
  SKIP_BRANCH_DRIFT-style overrides) bypass gates. Setting `TMPDIR` to a disk-backed dir did NOT help — the hook writes
  to `/tmp` directly, ignoring `TMPDIR`. Immediate mitigation applied this session: removed the three clearly-stale
  (>18h old) temp dirs + two abandoned parquets, taking `/tmp` from 100% → 8% (1.9GB free), after which the hook passed
  and the valid plan committed unchanged. The root cause (small 2GB tmpfs + no automatic reaper for agent/QG scratch +
  hook hardcoding /tmp) is unaddressed and WILL recur.
status: open
nature: notes
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [infra, tmpfs, disk-exhaustion, plan-hygiene, quality-gates, false-negative, fleet-blocker]
related: []
created: 2026-07-16
author: ikennaigboaka [slot-3·planning]
assigned_vm: planning
source:
  - slot-3 data_engineering session 2026-07-16 (task sports_data_sources_canonical_completion-027 — commit blocked by
    the spurious hook failure)
---

# Host /tmp tmpfs exhaustion → spurious plan-hygiene / QG failures

## What I found

- The orchestrator host's `/tmp` is a **2.0GB tmpfs** (`df -h /tmp` → `tmpfs 2.0G ... /tmp`). At 2026-07-16 ~01:28 UTC
  it was **100% full**.
- Real consumers (via `du -shx /tmp/*`): `/tmp/ao-debug-pull-20260715T074554Z` **806MB** (mtime 2026-07-15 07:47, ~18h
  old), `/tmp/tmpunbnn_2u` **425MB** + `/tmp/tmppljzkguo` **425MB** (both 2026-07-14, ~34h old),
  `/tmp/probe__index_availability_index.parquet` + `/tmp/detail_availability_index.parquet` **117MB each** (one-off
  analysis outputs). Three stale dirs alone = ~1.66GB.
- **Failure mode (the dangerous part):** with `/tmp` full, the pre-commit `plan-hygiene` hook's `check_frontmatter`
  (which pipes through `awk`) fails to write and emits
  `awk: (FILENAME=..._2026_07_13.md FNR=47) warning: error writing standard output: No space left on device`, then
  reports **false** `missing required field:` violations. I verified the plan's frontmatter was fully valid
  (`title/status/priority/parent_epic/estimate_class/estimate_baseline_ai_days/estimate_calibrated_ai_days/locked_by`
  all present) — the errors were entirely an artifact of the disk-full awk failure.
- `TMPDIR=<disk-backed dir>` did **not** work around it — the hook writes to `/tmp` directly.

## Why it matters

- **Fleet-wide silent commit blocker:** every slot on this host that stages a plan/codex/runbook file hits the same
  spurious failure while `/tmp` is full. The dashboard just shows agents unable to ship.
- **False-negative trap:** the bogus "missing frontmatter field" output actively misleads. An agent could "fix" valid
  frontmatter (introducing churn/regressions), loop, or reach for `SKIP_BRANCH_DRIFT=1`-style human-only overrides to
  force a commit — all wrong responses to what is actually a host disk-space problem, not a content problem.
- **Recurs by design:** a 2GB tmpfs with no reaper predictably refills from agent/QG scratch (debug pulls, parquet
  analysis dumps, QG logs). The immediate cleanup buys time, not a fix.

## Recommended decision

Pick a durable fix (not just re-clean each time). Candidates, cheapest first:

- **A tmp-reaper cron on the host** (e.g. `systemd-tmpfiles` / a small `find /tmp -maxdepth 1 -mmin +720 -delete`-style
  sweep guarded to skip live mounts like `tmux-*`, `mcp-*`, `uv-*.lock`, `.s.*` sockets) — clears >12h scratch
  automatically. Lowest effort, highest leverage.
- **Enlarge the tmpfs** (2GB → 8–16GB) if RAM headroom allows, and/or point large one-off analysis outputs at `/home`
  (50GB free on `/dev/root`) instead of `/tmp`.
- **Make the hooks fail LOUDLY and correctly on ENOSPC** — `check_frontmatter` (and any QG awk/python that writes tmp)
  should detect a write error and emit a clear "disk full — not a content violation" message instead of silently
  degrading into false frontmatter violations. This removes the trap even if `/tmp` fills again.

## Todos

- [ ] [INFRA] P1. Add a guarded `/tmp` reaper on the orchestrator host (sweep top-level entries older than ~12h,
      excluding live sockets/locks: `tmux-*`, `mcp-*`, `uv-*.lock`, `.s.*`, `systemd-*`) so the 2GB tmpfs cannot refill
      to 100% and silently block fleet commits. (repo: agent-orchestrator — host provisioning / cron)
- [ ] [INFRA] P2. Point large one-off analysis/debug scratch (availability-index parquets, `ao-debug-pull-*`) at a
      disk-backed dir under `/home` (or the per-slot scratchpad) instead of `/tmp`, so the small tmpfs is reserved for
      genuinely-ephemeral small files. (repo: agent-orchestrator + any scripts writing big /tmp outputs)
- [ ] [DATA] P2. Harden `scripts/plan-hygiene/check_frontmatter` (and QG steps that pipe through awk/python tmp writes)
      to detect an ENOSPC/write failure and emit an explicit "disk full — not a content violation, aborting" error
      instead of degrading into false `missing required field` violations that mislead agents. (repo:
      unified-trading-pm)
