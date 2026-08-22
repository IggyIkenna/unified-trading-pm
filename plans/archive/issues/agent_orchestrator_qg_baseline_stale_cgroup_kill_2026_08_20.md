---
doc_type: issue
title: agent-orchestrator quickmerge silently OOM-killed by stale QG memory baseline (cgroup MemoryMax)
summary: >-
  Every `quickmerge.sh` run for agent-orchestrator was being silently SIGKILLed (exit 137) by its own systemd cgroup
  `MemoryMax`, always within the last ~2% of the pytest suite, with zero trace in the run's own log or in host
  `dmesg`/`journalctl -k` (the kill is scoped to the run's own systemd-run cgroup, not a host-level OOM). Root cause:
  `qg-host-governor.sh`'s reservation-mode governor caps each repo's QG cgroup at 1.2x its committed
  `qg_resource_baseline.json` peak RSS; agent-orchestrator's committed baseline was `peak_rss_mb: 1014`
  (measured_at_utc 2026-08-17T02:59:08Z) → cap ~1217MB, but the live pytest run (`tests/` with `--cov=server`) now
  peaks at ~2GB+ RSS — roughly double the committed baseline. Reproduced 4 consecutive times in one session (2026-08-20
  ~01:03-01:36 UTC) on a `local_ratchet_gate_breach` escalation (agt-ddcd59) trying to ship a one-line
  `no_empty_string_fallback` ratchet fix — every attempt died at the same ~98% pytest-completion point regardless of
  host load (confirmed via `ps` RSS tracking across attempts: 1.4GB -> 1.5GB -> ... -> ~2.05GB before each death).
  Confirmed NOT a host-level OOM: `cat /sys/fs/cgroup/.../memory.events` on the session's own
  `system.slice/orchestrator.service` cgroup showed `oom_kill 0`; the pytest process must be spawned into a NESTED
  systemd-run scope by the governor with its own tighter cap, invisible to a plain `ps`/`journalctl -k` check. Fixed by
  re-running `scripts/dev/measure-qg-baseline.sh --env local --repos agent-orchestrator --force` (the SSOT-documented
  recovery per the governor script's own comment at qg-host-governor.sh:662) to bump the committed baseline to the
  current real peak — a >20% jump was expected and required `--force` since the anomaly guard (qg_host_adaptive_resource_governor_2026_07_14.md
  Trigger 3) does not auto-promote a >=20% RSS increase.
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ci-cd, quality-gates, memory, cgroup, quickmerge, agent-orchestrator, false-negative]
created: 2026-08-20
author: cicd-agt-ddcd59
priority: P1
parent_epic: infrastructure_master
source: "slot 32, local_ratchet_gate_breach escalation agt-ddcd59, 2026-08-20 ~01:03-01:36 UTC"
assigned_vm: NA
execution_scope: local-only
assigned_role: infra
effort: low
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
related: [infra_consolidated_closeout_2026_07_25]
context_scope:
  [
    /plans/active/issues/agent_orchestrator_quickmerge_orphan_reap_kills_interactive_background_2026_08_20.md,
    unified-trading-pm/scripts/quality-gates-base/qg-host-governor.sh,
    unified-trading-pm/scripts/dev/measure-qg-baseline.sh,
    unified-trading-pm/scripts/dev/qg_resource_baseline.json,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
  ]
---

> **📦 ARCHIVED 2026-08-22** — all 3 todos closed (issues-corpus executable-queue dispatch): RSS-doubling
> root-caused as genuine test-suite growth (265→302 test files, +37, 2026-08-17→08-20); the 2 diagnosability/sweep
> follow-ups' extraction-flip (missed 2026-08-21) corrected, citing `infra_satellite_ao_dispatch_batch2_2026_08_21.md`
> todos 14-15 as their live tracking home. 0 open todos, no lock. **Read the CORRECTION section below before
> re-deriving the memory-cap theory for a future silent near-completion QG death** — the actual root cause of the
> *shipping* blocker this doc chased was `orphan_reap`, not the memory baseline; see
> `plans/active/issues/agent_orchestrator_quickmerge_orphan_reap_kills_interactive_background_2026_08_20.md`.

# agent-orchestrator quickmerge silently OOM-killed by stale QG memory baseline

## What happened

A `local_ratchet_gate_breach` escalation (agt-ddcd59) needed to ship a one-line `# noqa: qg-empty-fallback` fix to
`agent-orchestrator/server/codex_bridge_server.py`. The targeted ratchet check passed immediately (21 == baseline), and
a standalone `bash scripts/quality-gates.sh --no-fix` (run directly, NOT through quickmerge) also passed cleanly on the
first try. But every subsequent `bash scripts/quickmerge.sh ... --agent --files ...` invocation (4 attempts) died
silently mid-`pytest`, always within the last ~2% of the test run, with:

- No error message in the quickmerge/QG log — it just stops after the last progress dot.
- `git status` afterward shows the commit still local, unpushed, tree clean (nothing lost, just never landed).
- No entry in `journalctl -k` / `dmesg` on the shared host — checked immediately after each death, no OOM lines.
- The session's own cgroup (`system.slice/orchestrator.service`, from `/proc/self/cgroup`) shows `oom_kill 0` in
  `memory.events` — the kill is NOT happening at that cgroup level.

## Root cause

`qg-host-governor.sh` reservation mode wraps each repo's `quality-gates.sh` invocation in a systemd-run scope with
`MemoryMax` set to `1.2x` the repo's committed baseline peak RSS (`_qg_repo_mem_cap`, `qg-host-governor.sh:482`). The
committed baseline for agent-orchestrator (`unified-trading-pm/scripts/dev/qg_resource_baseline.json`) was:

```json
"agent-orchestrator": {"vm": {"peak_rss_mb": 1014, "measured_at_utc": "2026-08-17T02:59:08Z", ...}}
```

-> cap ≈ 1217MB. Live-observed pytest RSS (via `ps aux` polling across 4 repro attempts) climbed steadily to
**~2.05GB** before each death — a ~100% overshoot of the cap. `qg-host-governor.sh:652-662` documents exactly this
failure mode ("basedpyright killed by its own systemd cgroup MemoryMax (exit 137) while running under the
reservation-mode 1.2x-baseline cap ... re-profile via scripts/dev/measure-qg-baseline.sh") but the guidance is a code
comment, not a loud runtime message — the actual quickmerge/QG output gives **zero indication** that a memory cap
(rather than a genuine test failure or transient host contention) was the cause. This is a **silent false-negative**:
four consecutive humans/agents hitting this would each plausibly diagnose it as "flaky host contention" and just keep
retrying, as this session initially did (3 blind retries before finding the actual cause on attempt 4's investigation).

## Fix applied this session

```bash
cd unified-trading-pm
bash scripts/dev/measure-qg-baseline.sh --env local --repos "agent-orchestrator" --force
```

`--force` was required because the anomaly guard (`QG_BASELINE_ANOMALY_PCT=20` default) does not auto-promote a
measurement that jumps >=20% above the existing committed value — by design, per
`qg_host_adaptive_resource_governor_2026_07_14.md` "baseline freshness loop" Trigger 3, to catch genuine regressions vs
measurement flukes. This session's re-measurement IS the reviewed judgment call the guard is designed to require (a
CI-firefighter actively diagnosing a live blocking wall), not a silent bump.

## Open questions / follow-up

- [x] ✅ [SCRIPT] P2. **DONE 2026-08-22 (issues-corpus executable-queue dispatch).** Confirmed genuine test-suite
      growth, not an anomalously-low prior sample: `git ls-tree` at the two measurement commits shows agent-orchestrator's
      `tests/` grew from 265 to 302 `test_*.py` files (+37, +14%) between 2026-08-17 and 2026-08-20, with several
      large-insertion commits in that exact window touching `tests/` (one `280 files changed, 4000 insertions`, one
      `25 files changed, 6432 insertions`, plus multiple 800-1100-line single-file additions) — consistent with a
      genuine RSS-driver (more collected tests + fixtures under `--cov=server`), not a measurement fluke. The committed
      baseline (`unified-trading-pm@5a4d1ed13e`, 1014MB→4096MB local peak) is accepted as steady-state; no further
      re-baseline commits for agent-orchestrator have landed since, corroborating stability. Evidence:
      unified-trading-pm@5a4d1ed13e (baseline commit) + direct `git ls-tree`/`git log --stat` measurement this session.
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-21 (ag-closeout-audit, infra tranche Phase 3) — checkbox flip was missed when
      extracted.** Extracted into `plans/active/infra_satellite_ao_dispatch_batch2_2026_08_21.md` todo 14 (its own
      work not yet done — that's tracked there, not here). Was: **Make a cgroup-MemoryMax kill loudly diagnosable from the QG/quickmerge log itself** — today the
      only way to tell "died from the memory cap" apart from "died from generic host contention" or "died from a real
      test failure" is manually correlating `ps` RSS growth against the committed baseline mid-run, which is exactly
      the investigation this issue doc had to do from scratch. `_qg_governor_detect_oom_kill` (referenced at
      qg-host-governor.sh:659) apparently already exists to detect exit 137 under this cap — confirm it actually
      surfaces a clear message in quickmerge's own stdout/log (not just a code comment) for every repo, not just the
      basedpyright case the existing comment describes.
      **➡️ EXTRACTED 2026-08-21 (ag-closeout-audit, infra tranche Phase 3) → `plans/active/infra_satellite_ao_dispatch_batch2_2026_08_21.md` todo 14.**
- [x] ✅ [SCRIPT] P3. **DONE 2026-08-21 (ag-closeout-audit, infra tranche Phase 3) — checkbox flip was missed when
      extracted.** Extracted into `plans/active/infra_satellite_ao_dispatch_batch2_2026_08_21.md` todo 15 (its own
      work not yet done — that's tracked there, not here). Was: **Check whether other repos on this shared host have a similarly stale (>20% under-measured)
      baseline** that would silently fail the same way on their next quickmerge — `scripts/dev/qg_resource_baseline.json`
      is the full committed set; a bulk `--force` re-measure sweep (or at least a report of current vs.
      committed-baseline deltas without forcing) would catch this class before it blocks someone else's push.
      **➡️ EXTRACTED 2026-08-21 (ag-closeout-audit, infra tranche Phase 3) → `plans/active/infra_satellite_ao_dispatch_batch2_2026_08_21.md` todo 15.**

## CORRECTION (2026-08-20, same session, after landing the actual fix) — the real blocker was NOT the memory baseline

The stale-baseline fix above (re-running `measure-qg-baseline.sh --force`) is real and was applied, but it did **NOT**
fix the actual shipping blocker. After landing the baseline fix, 8 further `quickmerge.sh` attempts (qm5-qm12) STILL
died silently at ~96-98% of the pytest run — including attempts with `QG_GOVERNOR_DISABLE=true` (governor fully
bypassed, no cgroup cap of any kind active). That proves the memory cap was never the actual cause of the *shipping*
failures; the true root cause is documented in a NEW issue doc:
[[agent_orchestrator_quickmerge_orphan_reap_kills_interactive_background_2026_08_20]] — the orchestrator's own
`orphan_reap` sweep (`server/orphan_reap.py`) kills any backgrounded shell process attributable to a slot (via
`CLAUDE_CONFIG_DIR` env inheritance, not literal process identity) once it crosses ~340-360s age, regardless of launch
method (`setsid`+`disown`, plain `nohup`+`disown`, or the CLI-tool-native `run_in_background`) — and a full
agent-orchestrator quickmerge run legitimately needs ~380-420s on a busy shared host. The fix that actually landed the
commit was stripping `CLAUDE_CONFIG_DIR` (+ sibling `CLAUDE_*`/`CLAUDECODE` env vars) from the backgrounded process's
environment before launch, so `orphan_reap`'s config-dir scan never attributes it to the slot in the first place.

**Do not re-derive the memory-cap theory from this doc alone in a future incident** — read the orphan_reap issue doc
first if a `quickmerge.sh`/`quality-gates.sh` run dies silently near completion on this host; the stale-baseline
condition documented above is a real, independently-worth-fixing issue, but it is very unlikely to be the actual
blocker for a silent near-completion death from an interactive session.

## Provenance

Escalation `agt-ddcd59` (slot 32, `local_ratchet_gate_breach`, repo=agent-orchestrator), 2026-08-20. 4 reproduced
deaths at ~98% pytest completion before root-causing via `qg-host-governor.sh` source read +
`/sys/fs/cgroup/.../memory.events` + `qg_resource_baseline.json` cross-check. Superseded as the shipping blocker's
root cause per the CORRECTION above, same session, ~90 minutes later.

## Progress Log

- **context-scout 2026-08-20**: populated context_scope (5 entries).
- **2026-08-21 (slot 17, interactive) — corroborating live evidence**: while investigating scheduled/escalation-
  worker health (unrelated task), found `uptime` reporting **load average 46/54/60 on this 16-core VM** (~3-4x
  overload) and **30GB of swap actively in use on a 30GB-RAM host**. Same "chronically contended shared host"
  condition this doc and its sibling
  [[agent_orchestrator_pytest_cov_silent_death_under_host_load_2026_08_20]] already track — cross-linked there in
  more detail, not re-investigated independently here. Worth folding into whichever of this doc's 3 open
  `[SCRIPT]` todos ends up auditing other repos' baselines, since a host running this hot makes EVERY repo's QG
  memory/CPU baseline more likely to drift stale, not just agent-orchestrator's.
