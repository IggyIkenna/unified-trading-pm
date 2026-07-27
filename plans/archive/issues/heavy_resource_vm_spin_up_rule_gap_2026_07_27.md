---
doc_type: issue
title:
  When-to-spin-up-a-VM rule gap — Heavy I/O exemption for planning-vm was mistaken for a heavy compute/memory exemption,
  letting an ad-hoc script cause a shared-host RAM-exhaustion incident
summary: >-
  A slot-15 ad-hoc scratchpad script (candle_coverage_gap.py, a whole-corpus candle-coverage analysis) ran directly on
  the shared planning-vm host — not via quality-gates.sh, not via any registered VM launcher — and grew to 15.8GB RSS
  over 21 minutes, driving the host to 24/30GB used / 0GB free / load avg 50 and degrading the AO orchestrator's own
  poll loop fleet-wide. Slack follow-up (2026-07-27, #main channel) surfaced 4 action items: (1) fix the VM-spin-up rule
  gap that let this happen, (2) add a host-resources panel to a UI, (3) investigate planning-vm disk usage, (4) build a
  per-slot memory cap/cgroup guard against unbounded in-memory ad-hoc analysis. This doc extracts and closes out all 4.
  Root cause of (1): two SEPARATELY-scoped rules each covered a different axis and neither covered this case — the
  "Heavy I/O never runs from the operator's local machine" rule (added 2026-07-24) is about GCS bandwidth from the
  operator's own laptop and explicitly exempts the planning-vm; QG_MEM_CAP (quality-gates-memory-governance.md,
  2026-05-15) caps pytest/basedpyright memory but ONLY when invoked through quality-gates.sh. An ad-hoc script run
  directly, outside both, had no guard at all. Two people in the Slack thread each recalled a DIFFERENT one of these two
  rules as "the" rule that should have prevented this — both were half right, which is exactly the gap.
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [infra, ram, memory, oom, shared-host, vm-launcher, heavy-io, cgroup, ad-hoc-scripts, quality-gates, fleet-wide]
related:
  [
    /plans/active/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md,
    /plans/active/issues/shared_host_tmp_tmpfs_full_2026_07_26.md,
    /plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/06-coding-standards/quality-gates-memory-governance.md,
  ]
created: 2026-07-27
priority: P1
parent_epic: infrastructure_master
source: "#main Slack channel, 2026-07-27 (incident bot + Ikenna + Harsh discussion, 05:11Z-09:24Z)"
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by: unified-trading-pm@3aa871da0
---

> **🟢 RESOLVED 2026-07-27** — all 4 Slack action items closed: rule gap fixed + wrapper built + verified live
> (`unified-trading-pm@3aa871da0`), UI panel confirmed already shipped (`agent-orchestrator@97a8334`), disk usage
> cross-linked to its existing P1 docs rather than duplicated. Archived per issue-doc-lifecycle (ACKED-INTO-CODE).

# "When to spin up a VM" rule gap — heavy compute/memory on the shared planning-vm

## What I found

An automated incident alert (`#main`, ~05:11Z) reported: shared-host RAM hit 24/30GB used, 0GB free, load avg 50; the
orchestrator's own poll + `/api/state` endpoints began timing out. Root cause: slot 15's ad-hoc scratchpad script
`candle_coverage_gap.py` (a whole-corpus candle-coverage analysis, PID 225751) had grown to **15.8GB RSS over 21
minutes** — loaded entirely in memory, run directly on the shared planning-vm host, not via `quality-gates.sh` and not
via any registered VM launcher. It was SIGTERM-killed as a protective action (memory recovered 24→8GB used, load 50→35);
no worker session or git state was lost.

The incident write-up asserted this "violates the heavy-I/O-on-VM HARD RULE." When the operator (Ikenna) checked the
actual rule text, that assertion turned out to be wrong: the rule (`/codex/05-infrastructure/vm-launcher-runbook.md` §
heavy-I/O, added 2026-07-24) reads:

> Heavy I/O never runs from the operator's local machine (HARD RULE, unconditional) — full-corpus GCS walks /
> manifest-index rewrites / >few-hundred-object renames go on a VM in-region, always ... does NOT apply to the
> human-planning or AO-orchestrator VMs (already cloud-hosted).

That rule is about GCS **bandwidth** from the operator's own laptop, and it **explicitly exempts** the planning-vm — by
design, since it was written specifically to stop a corpus-wide GCS walk from running through the operator's own metered
laptop connection (2026-07-24 incident, 48-67hr ETA over paid roaming data). Running the same walk ON the planning-vm
was always intended to be fine under this rule.

Harsh separately recalled a different rule: "there were a bunch of OOMs in early days of planning-vm, so had that rule
created so that these things don't happen on planning-vm." That rule is real —
`/codex/06-coding-standards/quality-gates-memory-governance.md` (`QG_MEM_CAP`, added 2026-05-15 after a 79.7GB-RSS
kernel-OOM incident that crashed VS Code + all 8 worker sessions) — but it is scoped ONLY to `pytest`/`basedpyright`
subprocesses invoked through `quality-gates.sh`'s `base-service.sh`. It never wrapped arbitrary ad-hoc scripts.

**So both recollections were half right, and the actual gap sat between them**: no existing rule bounded "an
agent-authored ad-hoc script, run directly (not via QG, not via a VM launcher), that materializes a whole corpus in
memory on the shared host." That is exactly the shape of `candle_coverage_gap.py`.

## Why it matters

- The shared planning-vm hosts N concurrent slot workers plus the AO orchestrator's own control loop. An unbounded
  ad-hoc script degrading that host degrades every slot at once and risks the orchestrator's own liveness, not just the
  offending slot's task.
- This is a genuine SSOT-contradiction-class finding (CLAUDE.md "Findings triage" — an SSOT contradiction is
  NOTIFY-OPERATOR-worthy): the incident's own auto-generated root-cause claim ("violates the heavy-I/O rule") was itself
  wrong, and two people separately misremembered which rule applied. That is a documentation gap, not operator/agent
  error — the fix is closing the gap, not re-explaining the existing rules.
- This is directly related to (but distinct from) the already-open P1
  `shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`, which covers the QG-governor-admission-vs-later-kill
  problem for `quality-gates.sh` runs specifically. This doc's root cause is upstream of that one: an ad-hoc script
  outside the QG path entirely, with zero governance in effect.

## The 4 action items from the Slack thread — audit + resolution

1. **Add a RAM/disk/CPU panel to the UI (`main` bot, 7:06am).** **AUDITED — ALREADY DONE.** `agent-orchestrator` commit
   `97a8334` ("feat(dashboard): live Host Resources panel (CPU/RAM/disk) pushed over /ws/vm-resources every 5s",
   2026-07-27 11:50, Harsh, `Quickmerge: agent`) shipped a complete backend probe (`server/host_resources.py`,
   stdlib-only `/proc/stat` + `/proc/meminfo` + `shutil.disk_usage`) → auth'd websocket endpoint
   (`server/routes/vms.py:169-193`) → live-rendering frontend panel (`dashboard/src/VmResources.tsx`, color-coded tiles)
   wired into the top of the dashboard layout (`dashboard/src/App.tsx:1231,1317`, alongside
   `HealthStrip`/`BacklogSummary`) — literally "top of the UI." Tests present (`VmResources.test.ts`,
   `test_host_resources.py`, `test_authenticate_websocket.py`). Already on `live-defi-rollout`, tree clean. **No further
   work needed.**

2. **Investigate why the agent violated the heavy-analysis-on-VM rule (Ikenna, 9:19am).** **DONE — this doc.** Root
   cause per "What I found" above: not a rule violation at all — a rule GAP. Neither the heavy-I/O rule nor QG_MEM_CAP
   covered this case. Fixed via:
   - `/codex/05-infrastructure/vm-launcher-runbook.md` — new § "Heavy COMPUTE/MEMORY on the shared planning-vm (HARD
     RULE, added 2026-07-27)": closes the gap with 3 explicit options (bound the read / cap it via a new wrapper /
     dispatch to a dedicated VM), citing this incident and the QG-mem-cap precedent it generalizes.
   - `/codex/06-coding-standards/quality-gates-memory-governance.md` — new "Scope — this is QG-only" section making the
     QG-only boundary explicit, cross-linking to the new rule above so the next person doesn't make the same half-right
     assumption Harsh's agent made.
   - `cursor-configs/CLAUDE.md` § "Launching VMs / infra?" — one-line pointer added ("That exemption is I/O-only...") so
     the distinction is visible in the lean index, not just in codex.

3. **Investigate planning-vm disk usage, reported ~92% (Harsh, 9:15am).** **AUDITED.** Live read-only check via AWS SSM
   (`aws ssm send-command` against `i-0c9b283b31d6b5ca7`, `ap-northeast-1`, mirroring `check-ao-backlog-status.sh`'s
   pattern) on 2026-07-27, confirms: `/` at **96% used** (278G/290G, 12G avail — actually worse than Harsh's "92%"),
   `/tmp` tmpfs at **100%** (2.0G/2.0G), swap 4.2/15Gi used, load average 9.4-13.13. **This is the SAME underlying
   condition already tracked** by two existing, heavily corroborated (10+ independent slot reports each) open P1 issue
   docs: `/plans/active/issues/shared_host_tmp_tmpfs_full_2026_07_26.md` and
   `/plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md`. Not duplicating — added a fresh dated
   corroboration (via an external SSM vantage point, not from an interactive slot session) to both docs' Progress Logs
   instead. **Update (same day, 09:58Z, slot-10's independent entry pulled in during this session's own quickmerge)**:
   root filesystem was actually EXPANDED (290G→484G) shortly after my reading, load dropped 13.13→7.24 — likely
   root-cause resolution, per that doc's own Progress Log. Not this doc's finding to claim; left to the two target docs'
   own lifecycle to declare resolved. Actual disk cleanup otherwise remains `[OPERATOR]`-gated in those docs (liveness
   of other slots' files isn't determinable from inside any one slot, and `block_destructive_commands.py` correctly
   refuses recursive deletes for autonomous workers regardless) — out of scope for this doc to resolve further.

4. **Build a per-slot memory cap/cgroup guard against in-memory whole-corpus analysis (incident bot, closing line).**
   **DONE — built and verified live.** New `scripts/dev/run-bounded-analysis.sh` (unified-trading-pm): generalizes
   `QG_MEM_CAP`'s exact `systemd-run --user --scope -p MemoryMax=... -p MemorySwapMax=0` cgroup mechanism to wrap ANY
   command, not just QG subprocesses. Default cap 4G (smaller than QG's 10G — an ad-hoc script needing more is itself a
   signal to bound the read or use a VM instead). Macos/non-systemd hosts degrade to an advisory warning (same posture
   as `QG_MEM_CAP`). **Verified against the real planning-vm** via SSM (running as the `ubuntu` user, the actual context
   slot sessions run under — running as `root` via a bare SSM shell has no lingering systemd `--user` session and
   reports `systemd-run` unavailable, which is a context artifact, not a real host gap): a 200M cap correctly `Killed` a
   500MB allocation with `MemoryMax=200M` cgroup-enforced, confirming the mechanism actually fires in production, not
   just in theory.

## Recommended fix path

- [x] ✅ [DOC] P1. Close the rule gap in `vm-launcher-runbook.md` (new § heavy-compute-on-shared-host) +
      `quality-gates-memory-governance.md` (new scope-clarification section) + `CLAUDE.md` pointer. Repo:
      unified-trading-pm. **Done when**: both codex docs cross-reference each other and CLAUDE.md's one-liner
      distinguishes the I/O axis from the compute/memory axis. Evidence: this session's commit (see Progress Log).
- [x] ✅ [SCRIPT] P1. Build `scripts/dev/run-bounded-analysis.sh` (generalized mem-cap wrapper) and verify it actually
      enforces on the real planning-vm (not just locally on macOS, where the cap silently no-ops). Repo:
      unified-trading-pm. **Done when**: a live SSM-run test against the planning-vm shows a process exceeding the cap
      gets cgroup-SIGKILLed. Evidence: this session — 200M cap killed a 500MB allocation on `i-0c9b283b31d6b5ca7`
      running as `ubuntu`.
- [x] ✅ [DOC] P2. Confirm the UI host-resources panel (Slack item 2) is actually complete before filing any follow-up
      work for it. **Done when**: backend probe + endpoint + frontend panel all verified present with file:line
      citations. Evidence: `agent-orchestrator@97a8334` (see item 1 above) — no further action needed.
- [x] ✅ [INFRA] P2. Cross-link the disk-usage claim (Slack item 3) to the existing open P1 disk docs rather than filing
      a duplicate, with one fresh corroborating measurement. **Done when**: both existing docs' Progress Logs carry a
      2026-07-27 entry citing the SSM-measured state. Evidence: see Progress Log below + the two target docs' own
      Progress Log entries.

## Progress Log

- 2026-07-27 (this session): Filed after extracting 4 action items from the `#main` Slack thread. Root-caused the actual
  gap (two correctly-scoped-but-non-overlapping rules, neither covering ad-hoc direct script execution). Shipped the
  codex rule fix (`vm-launcher-runbook.md` + `quality-gates-memory-governance.md` + `CLAUDE.md` pointer) and the
  `run-bounded-analysis.sh` wrapper, verified live against the planning-vm via SSM. Audited the UI-panel item and found
  it already fully shipped (`agent-orchestrator@97a8334`, same day, by Harsh — no action needed). Audited the disk-usage
  claim and cross-linked to the 2 existing open P1 docs rather than duplicating. All 4 action items closed; archiving
  this doc per issue-doc-lifecycle (ACKED-INTO-CODE).
