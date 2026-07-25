---
doc_type: issue
title:
  Sports curated-universe — 4 real leagues (Faroe Islands premier+cup, Wales premier+FAW championship) exist ONLY in
  slot-9's unpushed/diverged unified-api-contracts commit; origin's overlapping curated-universe commit duplicated 23/24
  of the same region but MISSED these 4, and slot-9's dead-worker worktree risks being reset (losing them)
summary: >-
  Two slots independently built the same "Western Europe / small UEFA nations" curated-universe batch in
  unified-api-contracts league_data_other.py. Origin/live-defi-rollout already landed one version (a04996fd, "add
  domestic curated-universe leagues for 16 Western Europe/small nations (UEFA, 42 entries)", +583 lines). Slot-9's
  worktree (host ip-172-31-5-118, .tabs/9) has a COMMITTED-but-UNPUSHED, diverged (1 ahead / 5 behind) commit 71d6a787
  ("add Western Europe/small UEFA nations curated-universe, 43 entries, 16 countries — WebSearch-verified
  top+below+cup", +606 lines) whose worker is DEAD (tmux_alive=false, last_ping 2026-07-25T04:15Z — the slot-9 100%-
  context-crash incident, ref ao_worker_context_lifecycle_gap todo 7). Main (agt-52bb99) did a READ-ONLY content compare
  of the two commits' added league_ids: 23 of ~24-27 are IDENTICAL (pure duplicate), so a blind rebase+push of 71d6a787
  would create duplicate entries — but slot-9's commit UNIQUELY adds 4 real leagues that the CURRENT origin tip (356
  curated leagues) still lacks (verified 0 occurrences each): FAROE_ISLANDS_PREMIER_LEAGUE, FAROE_ISLANDS_CUP,
  WALES_PREMIER_LEAGUE, WALES_FAW_CHAMPIONSHIP. So neither a blind push (dup corruption) nor a wholesale discard (loses
  the 4) is correct. Filed so the 4-league coverage is not lost if slot-9's dead worktree is reset to origin.
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: [sports, curated-universe, league-data, unified-api-contracts, duplicate-work, worktree, dead-worker]
related: [/codex/05-infrastructure/per-tab-worktrees.md, /plans/active/sports_consolidated_closeout_2026_07_19.md]
created: 2026-07-25
last_updated: 2026-07-25
priority: P2
parent_epic: sports_master
source: "main orchestrator (agt-52bb99) read-only content compare during poll loop, 2026-07-25 ~06:26"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# 4 Faroe/Wales curated leagues live only in slot-9's diverged unpushed commit (rest is duplicate of origin)

## Evidence (read-only, 2026-07-25 ~06:26Z, main agt-52bb99)

- File both commits touch: `unified_api_contracts/canonical/domain/sports/league_data_other.py` (+ the same two test
  files `tests/unit/sports/test_sports_structural_gaps.py`, `tests/unit/test_mvp_scope.py`).
- Origin/live-defi-rollout already has **a04996fd**
  (`feat(sports): add domestic curated-universe leagues for 16 Western Europe/small nations (UEFA, 42 entries)`, +583).
  Slot-9 `.tabs/9/unified-api-contracts` has **71d6a787**
  (`feat(sports): add Western Europe/small UEFA nations curated-universe (43 entries, 16 countries) — WebSearch-verified top+below+cup`,
  +606), committed, unpushed, 1-ahead/5-behind, dead worker.
- **Overlap: 23 league_ids identical** across the two commits (andorra_primera_divisio, cyprus__, estonia_cup,
  finland_suomen_cup, gibraltar__, iceland_cup, ireland__, latvia__, liechtenstein_cup, lithuania_cup, luxembourg__,
  malta__, northern_ireland_*, wales_welsh_cup, …). → blind rebase+push = duplicate entries.
- **Unique to slot-9 71d6a787, ABSENT from the current origin tip (356 curated leagues) — verified 0 occurrences each:**
  `FAROE_ISLANDS_PREMIER_LEAGUE`, `FAROE_ISLANDS_CUP`, `WALES_PREMIER_LEAGUE`, `WALES_FAW_CHAMPIONSHIP`.
- Unique to origin: none real (the lone diff hit was a regex artifact, not a league).

## Recommended resolution (neither blind-push nor wholesale-discard)

- [ ] [DATA] P2. Add ONLY the 4 missing leagues on top of origin's CURRENT `league_data_other.py` —
      `FAROE_ISLANDS_     PREMIER_LEAGUE`, `FAROE_ISLANDS_CUP`, `WALES_PREMIER_LEAGUE`, `WALES_FAW_CHAMPIONSHIP` —
      following the existing entry pattern (and the same top-flight/below/cup WebSearch-verification rigor slot-9 used),
      ship via quickmerge to unified-api-contracts. Do NOT rebase+push 71d6a787 wholesale (would duplicate the 23 shared
      leagues). **Done when**: the 4 league_ids resolve in the origin curated universe and the sports structural-gap
      tests pass. Cross-ref the two test edits in both commits (structural_gaps + mvp_scope counts) — bump those counts
      by +4, not +43.
- [ ] [INFRA] P3. After the 4-league add lands, slot-9's diverged worktree (`.tabs/9/unified-api-contracts`, dead worker
      last_ping 04:15Z) can be safely reset to origin/live-defi-rollout per the inherited-dirty-WIP rule (dead claim →
      inherit; here the committed work is fully superseded — 23 dup + 4 re-added properly — so nothing unique is lost,
      no violation of "never discard uncommitted work"). Liveness-gate first (confirm the slot-9 worker is still dead).

## Triage / charter note

Main diagnosed read-only and is charter-barred from pushing code/config (ships via quickmerge through a worker) and from
resetting another slot's worktree by hand. Filed P2 (data-coverage gap, small + precisely scoped) so the 4-league
coverage survives regardless of what happens to slot-9's dead worktree. This is duplicate-work fallout, not a data-
correctness defect in landed data. Cross-flagged to review (agt-c83ba7), who raised the divergence (msg 1964).
