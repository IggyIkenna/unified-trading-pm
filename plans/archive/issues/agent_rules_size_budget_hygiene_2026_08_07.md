---
doc_type: issue
title: >-
  Agent-rules size budget hygiene: CLAUDE.md trimmed + a 95% WARN threshold added; SUB_AGENT_MANDATORY_RULES.md is next
  (10,214/10,240 B, already past its own warn line) — trim + verify parity with condensed CLAUDE.md
summary: >-
  Same-session follow-on from the escalation-watchdog work: while shipping doc fixes, `check_agent_rules_size_cap.py`
  showed CLAUDE.md at 40,929/40,960 B — 31 B of headroom, essentially the hard cap, discovered only by accident. Trimmed
  CLAUDE.md to 37,136 B (~9.3% headroom) by condensing its two densest domain-index bullets (VM-launching,
  AG-reconciliation) to a headline directive + codex pointer — verified every fact being removed from CLAUDE.md already
  lives in the linked codex SSOT first (`grep`-confirmed per fact before deleting), so nothing was lost, only relocated
  one hop away. Then added a non-blocking WARN threshold at 95% of each capped file's size (`agent-rules-size-cap.py`,
  `unified-trading-pm@ca522a71cf`) specifically so this doesn't silently re-accelerate back to the wall before anyone
  notices next time. That WARN immediately fired on the SIBLING file: `SUB_AGENT_MANDATORY_RULES.md` is at 10,214/10,240
  B (26 B headroom, past its 9,728 B / 95% warn line) — the exact same pattern, one file over. Operator asked to trim it
  too, AND to verify it still mirrors every CLAUDE.md rule a spawned sub-agent needs (condensed to fit, not dropped) —
  since `SUB_AGENT_MANDATORY_RULES.md` is what's pasted verbatim at sub-agent spawn time (per CLAUDE.md's own "Agent
  behavior" section), a rule present in CLAUDE.md but missing from this file's condensed mirror is a rule a sub-agent
  can silently violate. This todo was interrupted before starting by a context-usage checkpoint hook (~65%) — nothing
  done yet on this specific item.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [claude-md, sub-agent-rules, size-cap, plan-hygiene, quality-gates]
related:
  - /codex/12-agent-workflow/plan-completion-and-archival-discipline.md
created: "2026-08-07"
author: interactive session (ikennaigboaka)
source: [interactive session, operator request after the CLAUDE.md size-budget emergency trim]
assigned_vm: NA
execution_scope: local-only
priority: P2
parent_epic: agent_operating_framework_master
drift_direction: advance-code
resolved_by: interactive session, 2026-08-07 — unified-trading-pm@3abd89e68c
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    cursor-configs/CLAUDE.md,
    cursor-configs/SUB_AGENT_MANDATORY_RULES.md,
    scripts/quality_gates/check_agent_rules_size_cap.py,
  ]
---

# Agent-rules size budget hygiene

> **🟢 ARCHIVED 2026-08-07 — RESOLVED** (status: resolved, 0 open todos, unlocked). All 3 items shipped as
> `unified-trading-pm@3abd89e68c`; both agent-rules files confirmed `[ ok]` by `check_agent_rules_size_cap.py`.
> Same-session archival per the completion-and-archival-discipline SSOT.

## What shipped already this session (context, not open work)

- `unified-trading-pm@bdbdcefc` — `check_terminal_status_archived.py --only <files>` (precommit-scoped, no ratchet math)
  wired into `run_hygiene_sweep.sh --precommit`; catches a staged terminal-status-and-unarchived doc at commit time
  (~0.06s) instead of hours later in full CI.
- `unified-trading-pm@6ffedce7` — CLAUDE.md 40,929 → 37,136 B. Condensed the "Launching VMs / infra?" and "RECONCILING
  an AG's estate…" bullets (the two densest in the file, ~3KB + ~2.4KB) to a headline directive + "READ the SSOT first"
  pointer. Every fact removed was `grep`-verified present in the linked codex doc(s) BEFORE deletion — see that commit's
  message for the verification trail.
- `unified-trading-pm@ca522a71cf` — added `WARN_RATIO = 0.95` to `check_agent_rules_size_cap.py`: a non-blocking WARN
  line in every `quality-gates.sh` run once a capped file crosses 95% of its hard cap, so size creep is visible many
  commits before the next emergency-trim situation. Immediately surfaced the `SUB_AGENT_MANDATORY_RULES.md` finding
  below — the mechanism works.
- Reusable lesson (not written up elsewhere, recording here so it isn't re-discovered the hard way): a
  `plan-commit-sha-evidence` QG failure citing a `<repo>@<sha>` that "doesn't resolve" can be a STALE LOCAL SIBLING
  CLONE, not a fabricated citation — `git fetch origin` in the cited repo's local checkout before assuming fabrication.
  Confirmed live: `unified-trading-ci@b498ec2` / `@892bb81` both resolved instantly after a plain fetch (verified via
  `gh api repos/.../commits/<sha>` first, to confirm they were real before touching anything). The remaining 2
  unresolvable citations (`unified-trading-pm@12832f77ab`, `@cc1309869`) are genuinely absent from GitHub and are
  exactly the pre-existing baseline (2) — not fixed, not mine, left as-is.

## Open work

- [x] [DOCS] P2. **Trim `SUB_AGENT_MANDATORY_RULES.md`** — `unified-trading-pm@3abd89e68c`. 10,214 → 9,422 B (~8.0%
      headroom below the 10,240 B cap, clear of the 9,728 B warn line). Condense-don't-drop: tightened wording across
      every section (merged redundant bullets, cut restated context, shortened parentheticals whose detail already lives
      at the cited SSOT) rather than deleting any distinct rule.
- [x] [DOCS] P2. **Cross-check `SUB_AGENT_MANDATORY_RULES.md` against the JUST-CONDENSED CLAUDE.md for rule parity** —
      `unified-trading-pm@3abd89e68c`. Diffed CLAUDE.md's always-on section rule-for-rule against the mandatory-rules
      file (the conditional domain index is deliberately out of scope — the file's own header says sub-agents
      conditional-load that themselves). Found and added the following gaps, each condensed to 1-2 clauses:
      **agent-memory-writes-are-BANNED** (was entirely absent — the single highest-risk gap, since a sub-agent has no
      other route to this HARD RULE); **pre-task plan/issue conflict-check** + **grep-then-READ** + **no
      `python3     <<EOF` heredocs**; **shared-host ≤2 full QGs / never bulk-kill another slot's QG**;
      **plan-destination ask-before-creating** + **read `task_template.md` first**; **plan-archival-on-completion**;
      **`Evidence:     cloudbuild=<id>`** runtime-verification convention; **no `*_SUMMARY.md` docs** +
      **`prettier-autostage.sh` only**; **never hand-raise a QG ratchet baseline**; **max 10 parallel sub-agents**.
      Deliberately left as pointer-only (sub-agent reads `CLAUDE.md`'s conditional index if the task actually touches
      it): data-pipeline- correctness heartbeat, commit-author-identity mechanics, full plan-frontmatter schema,
      cross-doc reference-path convention — none of these can be silently violated by a sub-agent that doesn't
      proactively read further, unlike the memory-ban and pre-task-conflict-check gaps, which bind by default.
- [x] [DOCS] P3. **Re-run `check_agent_rules_size_cap.py` after both items above** — confirmed `[ ok]` on both files:
      `cursor-configs/CLAUDE.md: 37,672 B / cap 40,960 B` and
      `cursor-configs/SUB_AGENT_MANDATORY_RULES.md: 9,422 B / cap 10,240 B`.

## Progress Log

- **2026-08-07 (interactive session)**: CLAUDE.md trimmed + WARN threshold shipped (3 commits above). Operator then
  asked to trim `SUB_AGENT_MANDATORY_RULES.md` too, with the parity check. Session hit a context-usage checkpoint (~65%)
  before starting that specific work — filed here per the commit-push-flip rule (every deferral is a tracked todo, not a
  chat promise) rather than risk it being lost to compaction.
- **2026-08-07 (same day, resumed after `/compact`)**: all 3 todos done, `unified-trading-pm@3abd89e68c`. Shipping hit
  one transient `quickmerge` failure — a lint violation (`F401` unused import) in
  `scripts/cicd/promote_fleet_startup_failure_monitor.py`, a file this session never touched. Checked its mtime before
  assuming it was safe to fix: 29s old at the time — a LIVE foreign-slot claim per the multi-agent-safety liveness rule
  (mtime <120s → PROTECT), not a stale/dead one, so it was correctly left alone rather than "fixed" out from under
  whoever was mid-edit on it. Retried `quickmerge` instead; STAGE 0.4's pull picked up that peer's now-completed,
  QG-clean commit, and the same command landed clean on the next attempt. All 3 open items done, 0 open, unlocked —
  archiving this doc now per the archival-on-completion rule captured in the parity trim above.
