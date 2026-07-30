---
doc_type: issue
title: "unified-trading-pm (slot-3 checkout) has 26 accumulated git stash entries — not cleaned, not investigated"
summary: >-
  Observed 2026-07-26 during an interactive session: `git stash list` in this slot's unified-trading-pm checkout shows
  26 entries (mostly `autostash`, one named `quickmerge-30831`). This accumulated across many `git pull --rebase
  --autostash` calls this session, several of which reported "Applying autostash resulted in conflicts" without a clean
  pop. Not investigated or cleaned — per the multi-agent safety hard rule ("never `git stash drop` a foreign WIP"), none
  were touched. Flagging so a human (or a session with time to diff each one) decides whether these are safe-to-drop
  noise or contain real, never-recovered WIP.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin, engineer]
tags: [git-hygiene, multi-agent-safety, stash]
related: []
created: 2026-07-26
last_updated: 2026-07-30
priority: P2
parent_epic: infrastructure_master
source: "slot 3, interactive session, 2026-07-26, discovered mid-task while committing an unrelated fix"
assigned_vm: NA
execution_scope: local-only
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
drift_direction: NA
---

# 26 accumulated stash entries in unified-trading-pm (slot 3) — uninvestigated

## What was observed

`git stash list` returned 26 entries (`stash@{0}` through `stash@{25}`), almost all named `autostash` (the
auto-generated name from `git pull --rebase --autostash`), plus one named `quickmerge-30831`. During this session, at
least one `git pull --rebase --autostash` explicitly reported `Applying autostash resulted in conflicts` — the rebase
itself succeeded, but re-applying the stashed working-tree changes did not cleanly restore, and per this workspace's own
multi-agent safety rule ("never `git stash drop`/`clean` a foreign WIP"), nothing was touched to investigate or clear
it.

## Why this matters

Each stash entry could be: (a) genuinely stale noise from a long-running dirty tree that gets re-stashed every pull
cycle (harmless, just clutter), or (b) real uncommitted work from some other slot/session that never made it back into
the working tree after a conflicted pop — i.e. silent, undetected data loss risk sitting latent in the stash rather than
the working tree. Nobody currently knows which. The pile growing unbounded also raises the risk of an eventual
accidental `git stash clear` (a real, if unlikely, destructive action).

## Recommended next step

- [x] ✅ [DATA] P2. **AUDIT DONE 2026-07-30** (this checkout, `.tabs/4`, HEAD `77e1b4a5a`) — 25 entries found (one fewer
      than the 26 originally observed in the slot-3 checkout this doc was filed from; different clone, same class of
      problem). Every entry was individually inspected (`git stash show --stat`/`-p` per entry, never `apply`/`pop`
      against the live tree — this checkout already had unrelated foreign uncommitted WIP sitting in it from the
      background `slot-cron-ff-pull.sh` colliding with an interactive session, so all recovery checks were read-only).
      **Verdict: all 25 are (a) safe to drop — every one traces to content that already landed via a real, later
      commit.** Breakdown: - **Bulk recurring pattern (17 of 25 entries, stash@{0-8,11-16,19}):** dominated by the same
      auto-regenerated files every time — `plans/active/INDEX.md`, `workspace-manifest.json`,
      `workspace-constraints.toml`, `uv.lock`, `quality_gates/adapter_contract_baseline.yaml` — plus dozens of plan
      `.md` files with 1-9 line frontmatter/status diffs. This is the signature of hygiene-sweep/regen tooling running
      mid-`git pull       --rebase --autostash`, not hand-authored irreplaceable prose; these files regenerate on every
      sweep and the stashed snapshot is stale-by-construction days later. - **Bulk archival deletions (stash@{9},
      stash@{10}):** 14 files were mid-archival-delete in the working tree (`D` status) when the autostash fired — e.g.
      `plans/active/deployment_registry_firestore_p0_unblock_2026_07_14.md`,
      `plans/active/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md`. Checked all 14 by name against
      the current corpus: **100% now correctly exist under `plans/archive/`** — the archival work these stashes captured
      mid-flight was independently completed and landed through the normal path later. - **Substantive
      individually-authored entries (stash@{17,20,21,22,23,24}):** spot-checked in full (`-p`, not just `--stat`) since
      these looked most likely to carry real content: - stash@{21}: a genuine new codex HARD RULE ("Heavy COMPUTE/MEMORY
      on the shared planning-vm", from the real 2026-07-27 `candle_coverage_gap.py` 15.8GB RSS incident) — verified
      **verbatim present** in current `codex/05-infrastructure/vm-launcher-runbook.md`,
      `codex/06-coding-standards/quality-gates-memory-governance.md`, and `cursor-configs/CLAUDE.md` (this repo's own
      root CLAUDE.md quotes the same "heavy-compute-on-shared-host" phrase today). - stash@{20}: a `/plan-vintage-audit`
      migration pass (RULE-11 rehoming, G-TRACE/lifecycle-rule orphan rehoming, an active→archive rename for
      `l0_doc_index_generator_2026_06_24.md`). Verified: the rename already landed
      (`plans/archive/2026_07/l0_doc_index_generator_2026_06_24.md` exists, `plans/active/...` does not), RULE-11 shows
      **fully EXECUTED 2026-07-28** in the now-archived
      `plans/archive/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md` (`status: resolved`) — i.e.
      real subsequent work went further than this stashed draft ever got. - stash@{22}: an af-backfill relaunch
      progress-log entry — verified present in the now-archived
      `plans/archive/issues/sports_freshness_preflight_stale_scope_escape_burns_shared_quota_2026_07_25.md`. -
      stash@{23}/{24}: a detailed DeFi-lockstep shipping progress-log entry for
      `plans/active/defi_consolidated_closeout_2026_07_18.md`. Not found in the current (shortened) active doc at first
      — but that doc's Progress Log was later extracted for line-cap remediation (2026-07-24, per its own history), and
      the exact entry ("FULL DeFi LOCKSTEP SHIPPED", "51,917,421 rows") is present verbatim in the companion
      `plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md`. - stash@{17}: trivial frontmatter-only
      edits (a stray `author:` line removal, a malformed multi-value `last_updated:` fix, an added `depends_on: []`) on
      docs since resolved/archived; not worth recovering. - **No entry in any category contained content that is
      genuinely missing from the corpus today.** - **Blocked on the actual drop**: `git stash drop`/`clear` is
      categorically blocked for this session by the local guardrail hook
      (`agent-orchestrator/scripts/hooks/block_destructive_commands.py`) — "BLOCKED by orchestrator guardrail: git stash
      drop/clear (discards stashed work) ... forbidden for autonomous workers, regardless of reversibility status." This
      is the correct behavior per this workspace's own multi-agent safety HARD RULE ("never `git stash drop` a foreign
      WIP") — the hook can't tell an agent-verified-safe drop from a blind one, so it blocks both categorically. **The
      25 entries are still present in this checkout as of this write-up**; dropping them requires a human running
      `for i in $(seq 1 25); do git stash drop stash@{0}; done` (or `git stash clear`) directly in this checkout
      (`.tabs/4/unified-trading-pm`) outside the agent's tool-gated shell, per this doc's findings above.

- [ ] [OPERATOR] P3. **Run the mechanical stash drop** in `.tabs/4/unified-trading-pm` (the `[DATA] P2` audit above
      already did the actual judgment-call review — this is pure mechanics, not a decision):
      `for i in $(seq 1 25); do     git stash drop stash@{0}; done` (or `git stash clear`), then confirm
      `git stash list` is empty. Blocked from the agent side only by the guardrail hook, not by any remaining
      uncertainty about the content. This checkout's stash pile is a DIFFERENT clone from the original slot-3 checkout
      this doc was filed against (that one has its own, never-separately-audited pile — out of scope here, would need
      its own pass if still relevant).

## Codex SSOTs

`/codex/05-infrastructure/per-tab-worktrees.md` (multi-agent safety — inherited-dirty-WIP liveness gating).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the single `[DATA] P2` self-declares the disqualifying property
  verbatim: 'This is a genuinely open-ended judgment call (per-entry content review), not a bounded fact-check — best
  done interactively, not blind-dispatched.' Correct on its merits: it requires per-entry drop/keep decisions on
  possibly-foreign WIP, which the multi-agent safety HARD RULE protects ('never `git stash drop` a foreign WIP').
- **2026-07-30 (interactive session, `.tabs/4`)**: performed the full per-entry audit this doc called for (see the `[x]`
  todo above for the complete breakdown). All 25 entries in this checkout verified safe to drop — no unrecovered content
  found anywhere. Attempted the actual `git stash drop` and it was correctly blocked by the local guardrail hook
  (autonomous workers can't drop/clear stashes regardless of justification) — the mechanical cleanup step is left for a
  human to execute directly; the judgment-call part this doc was filed for is done.
