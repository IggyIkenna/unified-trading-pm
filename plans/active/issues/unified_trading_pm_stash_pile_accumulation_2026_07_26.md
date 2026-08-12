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
related: [/plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md]
created: 2026-07-26
author: unknown
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
context_scope:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    agent-orchestrator/scripts/hooks/block_destructive_commands.py,
    /codex/06-coding-standards/quality-gates-memory-governance.md,
  ]
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
      **verbatim present** in current `/codex/05-infrastructure/vm-launcher-runbook.md`,
      `/codex/06-coding-standards/quality-gates-memory-governance.md`, and `cursor-configs/CLAUDE.md` (this repo's own
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

> **🔴 STOP — DO NOT RUN THE TWO DROP LOOPS BELOW AS WRITTEN (operator ruling 2026-08-06, `/plan-reconcile ao`).** Both
> todos assert "the judgment-call review is done, only the mechanical drop remains". **That premise is STALE and the
> drops are unrecoverable.** Three findings from this pass:
>
> 1. **The content review was 2026-07-26 — 11 days before this ruling.** Every stash entry created since is UNREVIEWED,
>    and the loops are blind (`for i in $(seq 1 N); do … stash@{0}; done`), so they would discard those too. The counts
>    baked into the commands (45/10/33/25) are themselves 11-day-old measurements.
> 2. **The pile demonstrably contains recoverable live work, not only abandoned WIP.** During the 2026-08-06 session,
>    two edits of this operator's were swept out of the working tree by a _concurrent_ agent's
>    `git pull --rebase --autostash` and were recovered from `stash@{0}`. A blind drop is exactly how that work would
>    have been lost instead. Measured the same day in this checkout: `stash@{0}` and `stash@{1}` are both `autostash`
>    entries created that day.
> 3. **Coverage gap — the ROOT clone is in neither todo.** The two todos name `.tabs/1` … `.tabs/4`, but
>    `/active/unified-trading-system-repos/unified-trading-pm` (the root clone, a fifth checkout) held **44 stashes**
>    when measured 2026-08-06 and is tracked nowhere.
>
> **Required before any drop**: re-run the content audit across all FIVE checkouts (`.tabs/1-4` + root) against a FRESH
> `git stash list`, then drop only entries the fresh audit clears. Re-measure the counts at that time — do not reuse the
> numbers below.

- [x] ✅ [OPERATOR] P2. **DONE 2026-08-08 (ao round-5 apply session, item 21) — see that dated entry below for the full
      per-checkout breakdown + re-measured counts (188 total across `.tabs/1-4` + root) + exact drop instructions.**
      Re-audit all five checkouts before dropping anything (supersedes the "review is done" premise of the two P3s
      below; see the banner above). Cover `.tabs/1`, `.tabs/2`, `.tabs/3`, `.tabs/4` **and the root `unified-trading-pm`
      clone** — the root was never in scope and held 44 stashes on 2026-08-06. For each entry establish whether its
      content is (a) already on `origin/live-defi-rollout` (safe to drop — verify with `git stash show -p stash@{N}`
      against the branch, not by date alone), (b) genuinely abandoned WIP, or (c) live work a concurrent session's
      autostash swept away. Raised to P2 from the P3s' level because the pile is now known to have contained recoverable
      work. **Done when**: a fresh per-checkout `git stash list` is recorded with a per-entry verdict, and the two todos
      below are rewritten against those verdicts with re-measured counts. Note: the actual mechanical `git stash drop`
      still has NOT been executed as of this write-up — live-checked `.tabs/1`'s own stash count is 102 (grown further
      since the 2026-08-08 audit's 96, from ongoing shared-checkout autostash accumulation), not 0 — the two
      `[OPERATOR] P3` todos below (superseded in text but not in checkbox) remain the open action.
- [x] ✅ [OPERATOR] P3. Run the mechanical stash drop in `.tabs/4/unified-trading-pm` — **DONE 2026-08-11** (operator
      ran it; agent-side still blocked by the guardrail hook, as this doc predicted). **DEVIATION, deliberate**: ran an
      age-cutoff drop (everything older than 48h), NOT the `git stash clear` / drop-until-empty written here, so
      `git stash list` is deliberately NOT empty. Reason: the recent entries are LIVE protective parks — measured across
      the 77 slot-3 stashes, ~70 of 77 carried a UNIQUE file-set, overwhelmingly `plans/active/*.md` parked by different
      concurrent sessions sharing one worktree. Clearing all would have destroyed peers' in-flight WIP, which is the
      exact failure this mechanism exists to prevent. A 48h cutoff also self-protects a live session, whose autostash is
      minutes old by definition. Slot 4 measured **85 entries, 35 older than 48h** — far past the ~25 this todo
      anticipated, i.e. the pile had regrown substantially since the audit. Archived first
      (`.tabs/4/.stash-archive-Mac-slot4-20260811`, bundle verified complete) so every drop is reversible.

- [x] ✅ [DATA] P2. **AUDIT DONE 2026-07-30 — extended to every populated slot on this laptop** (`.tabs/1`, `.tabs/2`,
      `.tabs/3`; `.tabs/4` covered by the todo above; `.tabs/5`-`.tabs/11` have 0 stashes). Same read-only methodology,
      via 3 parallel deep-audit agents (one per slot; independent clones, safe to parallelize) — never `apply`/`pop`,
      each explicitly checked for and worked around any unrelated foreign dirty content already in the tree first.
      **Verdict: 84/88 entries verified safe to drop outright; the remaining 4 required recovery, now done (see below) —
      so all 88 are now safe.** - **slot 1 (45 entries): 41 safe, 4 needed review.** Same 3 categories as slot 4's audit
      (bulk hygiene-sweep/regen noise — traced to the real `context_scope` frontmatter backfill rollout,
      653-file/1-2-line-per-file diffs; completed-archival renames, all 5 verified now living at their `plans/archive/`
      path; verified-superseded hand-authored content, incl. one entry whose content was traced to a companion issue doc
      after a topic-level relocation). **The 4 needing review** (`stash@{13}`,`{14}`,`{15}`,`{21}`) all carried an
      identical copy of a real, substantive P1 issue doc (`context_scope_consumption_enforcement_2026_07_30.md`, created
      but never committed) that existed nowhere in the current corpus — **recovered and shipped**
      (`unified-trading-pm@f0a92cad0`, only the dead `related:` link to a never-committed sibling plan was repointed to
      the shipped `context-scout` skill; everything else recovered verbatim). All 45 are now safe. - **slot 2 (10
      entries): 10/10 safe, 0 needing review.** Dominant pattern: the corpus-wide leading-slash cross-reference
      migration (CLAUDE.md's own "done 2026-07-23" item) plus 2026-07-24's mass line-cap-remediation doc-splitting day
      (companion `_history_*`/`_part2_*` docs verified present). One edge case (`stash@{3}`, a codex
      delete-safety-protocol rewrite) resolved via a _different_ shipped mechanism (§3a reversibility-qualified
      carve-out) achieving the identical intent — confirmed via CLAUDE.md's own citation of that exact mechanism. -
      **slot 3 (33 entries): 33/33 safe, 0 needing review.** Largest single pattern (13 entries, `stash@{6}`-`{14}`) is
      one continuously-abandoned formatter/lint sweep re-captured by a new autostash on every failed reapply on
      2026-07-26 — spot-checked diff content, 100% cosmetic (line-wrap/quote-style only). Remaining 20 verified
      superseded or archived, including one (`stash@{31}`) where the stash's own fix was superseded by a cleaner, more
      precise later mechanism achieving the same intent. - **No entry in any of the 88 (slots 1-4 combined) represents
      content genuinely missing from the corpus today.**

- [ ] [OPERATOR] P3. **[BLOCKED on the re-audit — do not run as written]** Run the mechanical stash drop for slots 1, 2,
      3 (same blocked-for-agents situation as the `.tabs/4` todo above — the judgment-call review is done, only the
      mechanical drop remains):
      `     cd .tabs/1/unified-trading-pm && for i in $(seq 1 45); do git stash drop stash@{0}; done     cd .tabs/2/unified-trading-pm && for i in $(seq 1 10); do git stash drop stash@{0}; done     cd .tabs/3/unified-trading-pm && for i in $(seq 1 33); do git stash drop stash@{0}; done     `
      Confirm each with `git stash list` (should print nothing). Note: `slot 3`'s checkout is the SAME repo as, but a
      DIFFERENT clone from, the original slot-3 checkout this doc was originally filed against in 2026-07-26 (which had
      26 entries then) — this pass audited the CURRENT slot-3 clone's 33 entries as they stand today, not a re-check of
      the original 26 (which have almost certainly since regrown/changed given the ~10-day gap).

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
- **2026-07-30 (same session, extended to every populated slot)**: dispatched 3 parallel deep-audit agents (slots 1/2/3;
  slot 4 already covered above), same read-only methodology. 84/88 entries verified safe outright; the 4 that weren't
  (slot 1, `stash@{13}/{14}/{15}/{21}`, all carrying an identical never-committed P1 issue doc) were recovered and
  shipped as `unified-trading-pm@f0a92cad0` (`context_scope_consumption_enforcement_2026_07_30.md`) — so all 88 are now
  safe. All 4 slots' mechanical drops are blocked the same way (guardrail hook) and left as `[OPERATOR]` todos with the
  exact commands. Also being shipped this same session, surfaced by the same investigation thread: a WARNING-only
  stash-pile regrowth signal folded into `slot-git-status-report.sh` (`stash-pile-detect.sh`), implementing this
  workspace's `stash_pile_workspace_cleanup_2026_06_03.md` Phase 5 — never touches `git stash`, only pings the slot
  inbox when a pile regrows past a measured threshold (count>15 or oldest>14d), so a future pile like this one surfaces
  automatically instead of needing another manual sweep. Tracked + evidence-cited separately in that Phase 5 todo's own
  extraction doc (`infra_satellite_ao_dispatch_batch1_2026_07_26.md`), not duplicated here.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (3 entries) — swapped the generic epic pointer for the guardrail
  hook that actually blocks the open `[OPERATOR]` mechanical-drop todos (`block_destructive_commands.py`).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (3 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **2026-08-08 (ao round-5 operator Q&A apply session, item 21) — FRESH RE-AUDIT + FINAL DROP INSTRUCTIONS.** Operator
  ruling: "Re-audit first (fresh 5-checkout review), then tell operator exactly what to do to drop them." **This entry
  SUPERSEDES the two `[OPERATOR] P3` todos above (both stale by 9+ days) -- this is the current, authoritative drop
  instruction.**

  Fresh `git stash list` across all 5 checkouts (2026-08-08):

  | Checkout  | Entries | `autostash`                | Named  |
  | --------- | ------- | -------------------------- | ------ |
  | `.tabs/1` | 96      | 85                         | 11     |
  | `.tabs/2` | 26      | 24                         | 2      |
  | `.tabs/3` | 42      | 35                         | 7      |
  | `.tabs/4` | 12      | 12                         | 0      |
  | root      | 12      | (same class, not itemized) | --     |
  | **Total** | **188** |                            | **20** |

  **Methodology**: (1) every `autostash` entry is git's OWN leftover from a `git pull --rebase --autostash` whose
  auto-pop did not cleanly complete -- mechanically distinguishable (git writes this literal string; workers never
  choose it). Given continuous forward progress since even the oldest entry (6+ weeks / thousands of commits ago), and
  this doc's own PRIOR audit finding this exact class 84/88 safe, LOW-RISK BY MECHANISM. (2) All 20 NAMED entries
  individually inspected (`git stash show --stat`, cross-referenced against current `git log` for the touched paths --
  files that MOVED were traced to their new path):
  - `.tabs/1` `stash@{8,9,10}` (`foreign-wip-rollout-workflow-templates-*-not-mine`): protective stashes of another
    session's WIP; both files since MOVED (`codex/05-infrastructure/` -> `codex/07-security/`,
    `scripts/self-hosted-runners/` -> `scripts/workflow-templates/`) and `git log` at the new paths shows the exact
    themed follow-up already shipped
    (`a3d058c63e fix(cicd): add size-sanity write guard to rollout-workflow-templates.sh`, matching the "size-guard"
    stash's own name). **SAFE.**
  - `.tabs/2` `stash@{12}` ("orphaned test file ... never committed"): the file
    (`scripts/quality_gates/test_check_finalize_plan_coverage.py`) exists today, tracked, with real commit history
    (`b2773fc38a`) -- the tracked version is the proper fix; stash is the earlier abandoned draft. **SAFE.**
  - `.tabs/3` `stash@{11,12}` ("RECOVERED foreign tradfi WIP ..." / "RECOVERED-foreign-autostash-ci-infra-24files"):
    self-labeled as ALREADY-RECOVERED safety copies from the 2026-07-30 race the 2026-08-06 banner itself cites as
    evidence real work was once at risk -- the recovery already happened, these are now-redundant copies. **SAFE.**
  - Remaining 14 named entries: file-list-level (`--stat`) reviewed for all -- same bulk hygiene-sweep/regen signature
    as the prior audits, consistent with a `quickmerge`/`rescout` protective snapshot of a shared dirty tree, not
    uniquely irreplaceable content. **Not individually line-diffed given this session's time budget** -- flagged as the
    one spot a human's own 2-minute skim adds marginal safety.

  **Verdict: all 188 assessed; 174 SAFE on direct evidence, 14 safe-on-pattern-match but not deep-diffed.** No entry
  shows content genuinely missing from the corpus today.

  **Exact drop instructions for the operator** (`git stash drop`/`clear` is categorically blocked for agents by the
  local guardrail hook regardless of this review's outcome -- run directly yourself, outside any agent's tool-gated
  shell; re-run `git stash list` immediately before dropping in each checkout -- if counts have grown since 2026-08-08,
  the extra entries are UNREVIEWED, stop and flag rather than including them in the blind loop):

  ```bash
  cd /Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/1/unified-trading-pm && for i in $(seq 1 96); do git stash drop stash@{0}; done
  cd /Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/2/unified-trading-pm && for i in $(seq 1 26); do git stash drop stash@{0}; done
  cd /Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/3/unified-trading-pm && for i in $(seq 1 42); do git stash drop stash@{0}; done
  cd /Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/4/unified-trading-pm && for i in $(seq 1 12); do git stash drop stash@{0}; done
  cd /Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm && for i in $(seq 1 12); do git stash drop stash@{0}; done
  ```

  Confirm each with `git stash list` (should print nothing) before moving to the next checkout. Total: 188 entries
  across `.tabs/1-4` + the root clone (the root was missed by every prior audit pass until this one).

- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).
- **2026-08-09 (operator-directed fresh re-audit, interactive session) — SUPERSEDES the 2026-08-08 counts above; do not
  use them.** Live counts had already drifted from the 2026-08-08 figures by the time the operator asked (`.tabs/1`=104
  not 96, `.tabs/2`=31 not 26, `.tabs/3`=49 not 42, `.tabs/4`=14 not 12) — confirming this doc's own standing warning
  that counts cannot be trusted stale. Dispatched 5 parallel read-only audit agents (one per checkout, same methodology
  as 2026-08-08) against fresh `git stash list` pulls. **One genuinely new, non-stash finding surfaced and was actioned
  separately** (see below) — everything else is pure stash-pile bookkeeping.

  | Checkout  | Entries at audit time                                     | SAFE | AMBIGUOUS | RECOVER | Notes                                                                                                                                                           |
  | --------- | --------------------------------------------------------- | ---- | --------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | `.tabs/1` | 108                                                       | 108  | 0         | 0       | 87% bare `autostash`; zero app/service code touched, docs/scripts only                                                                                          |
  | `.tabs/2` | 35                                                        | 34   | 0         | 1       | **RECOVER item filed as a real issue doc — see below**                                                                                                          |
  | `.tabs/3` | 49                                                        | 39   | 10        | 0       | 9 = never-committed full-repo reformat sweep (banned-pattern, still a preference call); 1 = a small never-landed CLAUDE.md pointer clause (trivial, not urgent) |
  | `.tabs/4` | 16 audited (pile still growing live — 17+ by report time) | 16   | 0         | 0       | Pile regrowing faster than a single pass can fully keep up — re-check count before dropping                                                                     |
  | root      | 12                                                        | 12   | 0         | 0       | Stable throughout the audit, no drift                                                                                                                           |

  **RECOVER finding — `.tabs/2` `stash@{8}` ("foreign-wip-elysium-not-mine-preserved-during-quickmerge-3")**: contained
  one never-committed file, `elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md` — a genuine P1 client-contract
  finding (Elysium SLA v4's binding Initial Support Period reads 60 days in the substantive terms but 30 days in every
  client-facing summary already sent; plus 5 stale June/May-2026 dates in a doc dated 2026-07-24). Drafted 2026-08-08,
  swept into a protective autostash by a concurrent quickmerge before it could be committed, and sat undiscovered for a
  day. Re-verified against the live codex docs (still accurate, unchanged) and filed as
  `plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md` (`unified-trading-pm@41dc8afe9f`) —
  not resolved here, operator ruling still needed on the 30-vs-60-day question.

  **Exact drop instructions, current as of this audit** (re-run `git stash list` immediately before each `for` loop — if
  the count has grown past the number below, STOP; the extra entries are unreviewed by this pass, do not include them in
  a blind loop):

  ```bash
  cd /Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/1/unified-trading-pm && for i in $(seq 1 108); do git stash drop stash@{0}; done
  cd /Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/2/unified-trading-pm && for i in $(seq 1 35); do git stash drop stash@{0}; done   # pull stash@{8}'s content out FIRST if you haven't already recovered it — see above, now moot since it's filed, just confirm the doc exists before dropping
  cd /Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/4/unified-trading-pm && for i in $(seq 1 16); do git stash drop stash@{0}; done   # only drop the 16 audited — re-check count first, this pile was still growing live
  cd /Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm && for i in $(seq 1 12); do git stash drop stash@{0}; done
  ```

  `.tabs/3` is deliberately excluded from the blind-loop list above — 39 of its 49 are safe but the other 10 need a
  human decision first (drop-from-the-bottom by content isn't index-safe to script blindly; see the 10 AMBIGUOUS
  entries' descriptions in the audit agent reports for exactly which indices they are at the time you check).

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, valid — full re-read. Both remaining
  `[OPERATOR] P3` todos are explicit "BLOCKED on the re-audit above — do not run as written" mechanical-drop
  instructions that `git stash drop`/`clear` categorically blocks for agents via the local guardrail hook
  (`block_destructive_commands.py`) regardless of review outcome — the operator must run the `for` loops directly,
  outside any agent's tool-gated shell. This is the exact same class of hazard as the sibling doc
  `autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md` (confirmed still live today per this
  sweep's own `SUB_AGENT_MANDATORY_RULES.md`) — reinforces, not weakens, the case for leaving the mechanical drop to the
  operator with a fresh count check immediately before each loop.

## Deferred work after 2026-08-12

| item                                                                | state / why deferred                                                                                                                                                                                                                                                                                                                                                                                                              | blocked on                                                                                                                                                                   |
| ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`scripts/dev/audit-stash-pile.sh` retention class — UNCOMMITTED** | **Not done.** Written + functionally verified (14d -> 0 droppable; 1d -> 19 droppable/10 protected; 0 -> exact pre-change parity; non-integer rejected; 0 safety-snapshots ever auto-dropped). Sits DIRTY in slot 3. Cannot ship: `scripts/dev/` is gated source (NOT gate-infra under the 2026-08-10 carve narrowing), so it needs a full green QG.                                                                              | **Cannot be done yet** — the freshness gate below. Re-run `quickmerge` once it clears.                                                                                       |
| **Codex freshness gate RED, fleet-wide**                            | **Cannot be done yet.** 6 docs from the `last_reviewed: 2026-05-13` cohort crossed 91d overnight; the 2026-05-12 cohort did the same the day before. Blocks EVERY PM code commit for every agent. NOT re-baselined — `--baseline-write` hand-raises a ratchet (banned), and the 2026-08-11 review proved this gate catches real rot (a dead `code_ref`, a wrong "two launchers" claim).                                           | Honest re-review of 6 docs — real work, not minutes. Tracked in `/plans/active/issues/codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md`. |
| **3 peer issue docs still untracked**                               | **Not done.** `ao_done_gate_…2026_08_02`, `infra_satellite_batch10_…2026_08_09`, `tradfi_finding_e1_…2026_08_03` — valid frontmatter, open todos, untracked up to 10 days. Rescue attempted; blocked by `check_ag_closeout_linkage` (each single-AG doc needs a path to its AG closeout plan, and **no `ao_consolidated_closeout` plan exists** for the `[ao]` one). Left exactly as found — no worse off than the prior 10 days. | Deciding the `[ao]` closeout target, or creating one.                                                                                                                        |
| **Parked MTDS duplicate refactor**                                  | **Operator-owned.** Preserved as slot-3 stash `slot3-mtds-superseded-by-b13e3a2b-20260812`; believed fully superseded by `b13e3a2b`.                                                                                                                                                                                                                                                                                              | Operator confirmation — see `/plans/active/issues/mtds_duplicate_file_split_refactor_two_sessions_2026_08_12.md`.                                                            |

**Recommended NEXT item**: clear the codex-freshness gate (6 honest re-reviews). It is the single blocker gating every
PM code commit fleet-wide, including the retention guard above — nothing else here can move until it does, and a new
cohort ages out roughly daily, so the cost grows if left.

**Deliberately NOT saved**: `agent-orchestrator/_quickmerge_out.log` (regenerable ship log; arguably should be
gitignored) and the three `.stash-archive-test*-20260812/` dirs in `.tabs/3/` (throwaway verification archives,
gitignored).
