---
doc_type: issue
title:
  "`locked_by: live-defi-rollout` — a branch name (not a person/session) stamped as the locker identity on 62 active
  docs, 18 of them with a `locked_since` date that predates the doc's own creation"
summary: >-
  Found while reconciling the `ao` tranche (plan_reconciler agt-fe4564, 2026-08-09): two non-grace `ao` docs
  (`deepseek_claude_blended_provider_routing_2026_07_28.md`, `long_lived_vm_logs_not_backed_up_2026_07_02.md`) carry
  `locked_by: live-defi-rollout` — the shared workspace branch name, not a plausible per-doc human/session locker
  identity — with `locked_since: 2026-05-21`, a date that PREDATES each doc's own `created:` field by weeks. A
  corpus-wide verification (`grep -rlE '^locked_by:\s*live-defi-rollout\s*$' plans/active/`, run directly this session,
  not assumed) found 62 active docs total carry this exact `locked_by:` value. Of those 62: 18 have `locked_since:
  2026-05-21` provably predating `created:` (impossible for a genuine lock — same exact date on every one, strongly
  suggesting a stamped default rather than 18 independent lock events); 19 have a blank `locked_since`; 25 have a
  `locked_since` on or after `created:` (plausible on date-logic alone, not independently confirmed genuine).
  `locked_by:` is a HARD archival blocker no autonomous agent may clear without an explicit `[unlock-plan]` — if this is
  a tooling bug rather than genuine intent, it could be silently blocking legitimate archival across a meaningful slice
  of the corpus.
status: open
nature: issue
asset_group: [ao, infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [locked_by, corpus-wide, tooling-bug, archival-blocker, plan-hygiene]
related:
  [
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/active/issues/long_lived_vm_logs_not_backed_up_2026_07_02.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-09"
author: plan_reconciler
priority: P1
parent_epic: plan_hygiene_master
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: review
drift_direction: none
depends_on: []
assigned_vm: NA
execution_scope: local-only
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/active/issues/long_lived_vm_logs_not_backed_up_2026_07_02.md,
  ]
source: "plan_reconciler agt-fe4564 (slot 21), ao-tranche reconciliation run, 2026-08-09"
---

# `locked_by: live-defi-rollout` bogus-lock pattern — corpus-wide

## What I found

Two docs in this run's `ao`-tranche batch both carried the exact same suspicious signature:

- `plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md`: `locked_by: live-defi-rollout`,
  `locked_since: 2026-05-21`, `created: 2026-07-28`.
- `plans/active/issues/long_lived_vm_logs_not_backed_up_2026_07_02.md`: `locked_by: live-defi-rollout`,
  `locked_since: 2026-05-21`, `created: "2026-07-02"`.

`live-defi-rollout` is the shared integration branch every slot commits to (per `CLAUDE.md` § "Multi-agent safety") —
not a person, a session id, or an agent identity. And `2026-05-21` cannot be a genuine lock timestamp on either doc:
both locks are dated 7-10 weeks BEFORE the doc they're attached to was even created. This reads as a stamped default
value, not two (or more) independent human lock actions that happened to land on the identical date.

**Corpus-wide verification, run live this session** (not assumed from the 2 samples):

```
grep -rlE "^locked_by:\s*live-defi-rollout\s*$" plans/active/ | wc -l
# => 62
```

Breaking the 62 down by `locked_since` vs `created:`:

| Bucket                                                   | Count  | Confidence                                                                        |
| -------------------------------------------------------- | ------ | --------------------------------------------------------------------------------- |
| `locked_since: 2026-05-21`, provably predates `created:` | **18** | **Confirmed bogus** — impossible for a genuine lock, same date on every one       |
| `locked_since:` blank                                    | 19     | Suspect (blank + branch-name locker is still unusual) but not provably impossible |
| `locked_since:` on/after `created:` (plausible)          | 25     | Not independently confirmed either way — date logic alone doesn't rule it out     |

**Note on methodology**: two hunter sub-agents in this run's fan-out independently flagged this pattern from their own
reading and estimated the corpus-wide count at "97" via `grep -rl "locked_by: live-defi-rollout"` (no line anchors).
Re-running that exact grep against the current corpus returns 62, not 97 — I could not reproduce 97 with either the
anchored or unanchored pattern. The 62/18/19/25 breakdown above is what I directly measured this session; treat 97 as an
overstated estimate from a sub-agent, not a confirmed figure.

## Why it matters

- `locked_by:` is one of the few HARD, human-only gates in this workspace: "An explicit human signal: `locked_by:` is a
  person saying 'not yours' — `[unlock-plan]` is theirs to give" (`cursor-configs/skills/plan-reconcile/SKILL.md` §
  "STILL ASK/PARK"). No autonomous agent — including this one — may clear it, however confident the evidence.
- If this is a tooling/migration bug (most likely explanation given the identical date across every predating case), it
  means at least 18 docs — and plausibly more of the other 44 — cannot be auto-archived even once genuinely complete,
  silently piling up in `plans/active/` and inflating every hygiene-sweep/inventory count.
- Neither of the 2 docs that surfaced this (both named above) is otherwise problematic — the deepseek routing doc has 6
  open / 24 done todos (not archive-ready regardless); the VM-logs doc has 1 open / 2 done (near-complete, and the bogus
  lock is the ONLY reason it isn't already a clean archive-or-consolidate candidate once its 1 remaining todo closes).

## Recommended next steps (operator ruling needed — this is a judgment call, not evidence-resolvable)

- **Option A** — bulk-clear `locked_by:`/`locked_since:` on the 18 confirmed-predating docs only (highest-confidence
  subset), leave the other 44 for a follow-up once someone confirms whether ANY of them are genuine.
- **Option B** — bulk-clear all 62 (branch-name-as-locker is itself already anomalous regardless of date logic), on the
  theory that a genuine human lock would never use the branch name as the locker identity in the first place.
- **Option C** — before clearing anything, find and fix the root cause (likely a template default or a migration script
  that stamped this) so it stops recurring, THEN clear the backlog it already produced.
- **[WORKER REC]**: **C first, then A** — fixing the root cause prevents this from silently growing further, and the 18
  confirmed-impossible cases are safe to clear with no ambiguity; the other 44 deserve a second look once the producing
  mechanism is understood (it may explain which of them are real).

## Related doc-drift noticed along the way (this run's ao-tranche pass, filed here for a single operator touchpoint)

- [ ] [DOCS] P2. **CLAUDE.md still instructs `sudo bash scripts/install-<job>-timer.sh`** (under "AO scheduled jobs") —
      `ao_scheduled_job_reserve_and_staggering_2026_08_04.md`'s own shipped fix (agent-orchestrator@c3a85c3b4,
      2026-08-08) converted all 8 installers to `systemd --user`, which now hard-ERRORs under `sudo`. Both
      `unified-trading-pm/CLAUDE.md` and the `cursor-configs/CLAUDE.md` it's symlinked from need the one-liner updated
      to drop `sudo`. Out of plan_reconciler's edit authority (not under `plans/**`).
- [ ] [DOCS] P3. **`codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`** documents
      `POST     /api/slots/{id}/rotate-account` as live; confirmed via
      `deepseek_claude_blended_provider_routing_2026_07_28.md` (grepped `routes/slots_ops.py`/`server.py` directly,
      2026-07-28) that no such route exists — real mechanism is `reassign`+`spawn`. Needs an operator ruling before any
      agent edits this codex SSOT (HARD GATE).
- [ ] [DOCS] P3. **`codex/05-infrastructure/per-tab-worktrees.md`** doesn't document `cascade_dep_branch()`'s TOCTOU
      race (root-caused in `utl_shared_clone_commits_repeatedly_reset_2026_07_22.md`, 3 recurring incidents, partial fix
      shipped, 3 stronger fixes operator-authorized 2026-08-08 but not yet implemented) despite that doc's own banner
      citing `per-tab-worktrees.md` as the governing SSOT for exactly this mechanism.
- [ ] [DOCS] P3. **`codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`** cites
      `plans/active/issues/ao_operator_delete_gating_aws_iam_and_corpus_sweep_2026_07_27.md` as "will archive; this doc
      is the durable SSOT going forward" — that doc is now archived at
      `/plans/archive/issues/ao_operator_delete_gating_aws_iam_and_corpus_sweep_2026_07_27.md`; the codex doc's own
      reference is dangling (path-only fix, but codex is out of `plans/**`).

## Progress Log

- 2026-08-09 (plan_reconciler agt-fe4564, slot 21, ao-tranche run): Filed. Corpus-wide count independently verified live
  this session (62, not the 97 two hunter sub-agents estimated); predate-vs-created breakdown computed directly from
  frontmatter, not sampled. Not fixed — `locked_by:` is a human-only gate. Routed via `/blocked` for an operator ruling
  on remediation option (A/B/C above).
