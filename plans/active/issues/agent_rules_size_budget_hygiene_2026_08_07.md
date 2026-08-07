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
status: open
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
resolved_by:
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

- [ ] [DOCS] P2. **Trim `SUB_AGENT_MANDATORY_RULES.md`** (currently 10,214/10,240 B, past its new 9,728 B / 95% warn
      line) — same condense-don't-drop discipline as the CLAUDE.md pass: find genuinely compressible wording/resolved
      history, verify any relocated detail already lives in its cited SSOT before cutting it from this file. Target:
      meaningful headroom below the WARN line (mirror today's ~9-10% margin on CLAUDE.md), not just squeaking under.
- [ ] [DOCS] P2. **Cross-check `SUB_AGENT_MANDATORY_RULES.md` against the JUST-CONDENSED CLAUDE.md for rule parity** —
      this file is pasted verbatim at sub-agent spawn time (CLAUDE.md § "Agent behavior": "paste
      `SUB_AGENT_MANDATORY_RULES.md` at spawn top"), so any HARD RULE a spawned sub-agent must not violate needs to
      exist here too, condensed to fit, never silently dropped because CLAUDE.md already states it — a sub-agent never
      reads CLAUDE.md directly. Diff the two files' rule sets (not prose-for-prose, rule-for-rule) and confirm: every
      CLAUDE.md HARD RULE that could plausibly bind a sub-agent's actions (git discipline, quality gates, findings
      triage, plan authoring it might touch, multi-agent safety) has a corresponding line in
      `SUB_AGENT_MANDATORY_RULES.md`. Gaps found → add the missing rule (condensed) before trimming anything else, so
      the trim doesn't net-negative sub-agent rule coverage while fixing the byte count.
- [ ] [DOCS] P3. **Re-run `check_agent_rules_size_cap.py` after both items above** and confirm `[ ok]` (not `[WARN]`) on
      both files before considering this closed.

## Progress Log

- **2026-08-07 (interactive session)**: CLAUDE.md trimmed + WARN threshold shipped (3 commits above). Operator then
  asked to trim `SUB_AGENT_MANDATORY_RULES.md` too, with the parity check. Session hit a context-usage checkpoint (~65%)
  before starting that specific work — filed here per the commit-push-flip rule (every deferral is a tracked todo, not a
  chat promise) rather than risk it being lost to compaction. Next session: start with todo 1.
