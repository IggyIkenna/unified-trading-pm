---
doc_type: issue
title:
  CLAUDE.md's "Shared-host ≤2 full QGs" line doesn't say it's auto-enforced — leads agents to hand-poll instead of just
  invoking quality-gates.sh
summary: >-
  CLAUDE.md's Git-discipline section states "Shared-host ≤2 full QGs at once (max(2, floor(cores/4)))" as a bare
  capacity fact, with no mention that `quality-gates.sh` already enforces this itself via a flock-based host governor
  (`qg-host-governor.sh`, fully documented in `/codex/06-coding-standards/quality-gates.md` §"QG-sweep batching +
  shared-host concurrency") that blocks/queues automatically and excludes queue-wait from the `MAX_DURATION` timeout. A
  reasonable reading of the CLAUDE.md line is "the agent must manually pre-check capacity before invoking the script" —
  which is the wrong, more expensive interpretation.
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [claude-md, quality-gates, qg-governor, documentation, process]
related: []
created: "2026-08-09"
last_updated: "2026-08-09"
author: slot-5 (data_engineering)
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.05
estimate_calibrated_ai_days: 0.02
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope: [/codex/06-coding-standards/quality-gates.md]
source: >-
  Filed during the `/pre-compact` audit of session work on
  /plans/active/issues/cefi_chain_drop_v2_dedup_stop_on_surprise_198k_lossy_groups_2026_08_08.md todo 4 (2026-08-09,
  slot-5) — see that doc's Progress Log for the shipping session this was discovered in.
resolved_by:
locked_by:
---

# CLAUDE.md's QG-concurrency line omits that it's auto-enforced

## What I found

Working `/plans/active/issues/cefi_chain_drop_v2_dedup_stop_on_surprise_198k_lossy_groups_2026_08_08.md` todo 4
(2026-08-09), I hit a busy shared host (multiple slots' full QG runs already active) before shipping a fix. CLAUDE.md's
only guidance is:

> Shared-host ≤2 full QGs at once (`max(2, floor(cores/4))`); never bulk-kill another slot's `pytest`/QG.

Read literally, this reads as an agent responsibility to check before invoking `quality-gates.sh` — so I spent ~40
minutes hand-polling host process counts (twice, the first attempt was imprecise) before discovering the script already
has a built-in `flock`-based concurrency governor (`scripts/quality-gates-base/qg-host-governor.sh`) that blocks/queues
automatically at exactly this K, and excludes governor queue-wait from the `MAX_DURATION` timeout check — i.e. just
invoking `quality-gates.sh` normally is always safe, no manual pre-check needed. This mechanism is fully and accurately
documented in `/codex/06-coding-standards/quality-gates.md` (the "QG-sweep batching + shared-host concurrency" section,
~180 lines) — the codex doc is NOT missing anything; the gap is purely that CLAUDE.md's condensed pointer line doesn't
say "auto-enforced" or point to the mechanism, so an agent that trusts the terse CLAUDE.md line alone (as intended —
that's the whole point of the L0 index) doesn't know to skip manual polling. Two other slots observed the same session
appeared to be independently working around the same contention with an ad-hoc (and in one case non-existent/no-op,
`PYRIGHT_TIMEOUT`) environment variable rather than the governor's own sanctioned
`--ignore-timeout`/`IGNORE_TIMEOUT=true` escape hatch — suggestive this is not a one-off misunderstanding.

## Why it matters

Small but real, recurring cost: every agent that hits host contention and doesn't already know about the governor
re-derives (or fails to derive) the same "just invoke it, it queues safely" realization from scratch, at the cost of
however long they spend hand-polling or reaching for un-sanctioned workarounds instead.

## Recommended decision

One-line CLAUDE.md clarification (size-budget-neutral if something else is trimmed to compensate — CLAUDE.md is
QG-enforced ≤40KB): change the existing line to note the mechanism is automatic, e.g. "Shared-host ≤2 full QGs at once,
auto-enforced by `quality-gates.sh`'s own governor (`max(2, floor(cores/4))`, queues rather than fails — just invoke
normally); never bulk-kill another slot's `pytest`/QG." Left to a follow-up rather than done inline here to avoid a
hasty edit to a shared, size-capped, high-traffic file under this session's own time pressure.

## Todos

- [ ] [DOC] P3. Clarify the "Shared-host ≤2 full QGs at once" line in `CLAUDE.md` (§ Git discipline + shipping pipeline)
      to note it is auto-enforced by `quality-gates.sh`'s built-in `qg-host-governor.sh` (flock token bucket) — agents
      should just invoke the script normally, no manual capacity pre-check needed. Keep net size neutral (trim elsewhere
      if needed) per the file's QG-enforced ≤40KB cap. (repo: unified-trading-pm)

## Progress Log

- **2026-08-09 (slot-5, data_engineering)** — Filed during `/pre-compact` while auditing session lessons for
  `cefi_chain_drop_v2_dedup_stop_on_surprise_198k_lossy_groups_2026_08_08.md` todo 4. Not fixed inline (small, but a
  shared size-capped file deserves a deliberate edit, not a rushed one under session-end time pressure).
