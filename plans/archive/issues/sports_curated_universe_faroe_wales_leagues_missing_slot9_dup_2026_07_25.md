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
status: resolved
nature: issue
asset_group: [sports]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: [sports, curated-universe, league-data, unified-api-contracts, duplicate-work, worktree, dead-worker]
related: [/codex/05-infrastructure/per-tab-worktrees.md, /plans/active/sports_consolidated_closeout_2026_07_19.md]
created: 2026-07-25
last_updated: 2026-07-26
priority: P2
parent_epic: sports_master
source: "main orchestrator (agt-52bb99) read-only content compare during poll loop, 2026-07-25 ~06:26"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by: "slot-5, 2026-07-26, uac@40d2dd8f750a96ff0a811b6b56f0ab5401d8ed87"
locked_by:
depends_on: []
---

> **🟢 RESOLVED 2026-07-26** — the one genuinely-missing league (`WALES_FAW_CHAMPIONSHIP`) was added
> (`uac@40d2dd8f750a96ff0a811b6b56f0ab5401d8ed87`); the other 3 named leagues turned out to already exist under
> different keys. Archived per the terminal-status-archived rule. No further action needed on this doc.

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

- [x] ✅ [DATA] P2. **DONE 2026-07-26 (slot-5) — uac@40d2dd8f750a96ff0a811b6b56f0ab5401d8ed87. CORRECTION: only 1 of the
      4 named leagues was actually missing.** This doc's "verified 0 occurrences each" check (Evidence section above)
      matched on exact `league_id` KEY STRINGS only — it did not check whether the same real-world league already
      existed under a DIFFERENT key. Re-checked via `api_football_id` (the source-catalog identity) against the current
      origin tip: `FAROE_ISLANDS_PREMIER_LEAGUE` (id=367) is the SAME league as origin's existing
      `FAROE_ISLANDS_MEISTARADEILDIN`; `FAROE_ISLANDS_CUP` (id=491) is the SAME as origin's existing
      `FAROE_ISLANDS_LOGMANSSTEYPID`; `WALES_PREMIER_LEAGUE` (id=110) is the SAME as origin's existing
      `WALES_CYMRU_PREMIER`. Adding any of these 3 under slot-9's key names would have created true `api_football_id`
      duplicates for one real league. Only `WALES_FAW_CHAMPIONSHIP` (id=111) was genuinely absent — confirmed by the
      clean 110/111/112 id progression bracketing it between origin's existing tier-1 and cup Wales entries. Added that
      one entry (slot-9's WebSearch-verified field values), bumped both structural-gap test counts by +1 (not +4). 1271
      sports/league tests green, full `quality-gates.sh` PASSED.
- [x] ✅ [INFRA] P3. **CONFIRMED MOOT 2026-07-26 (slot-5).** `.tabs/9/unified-api-contracts` was ALREADY reset to
      origin/live-defi-rollout cleanly (0 ahead/0 behind, no dirty working tree, HEAD=`b0547c36`) before this session
      started — no reset action was needed.

## Triage / charter note

Main diagnosed read-only and is charter-barred from pushing code/config (ships via quickmerge through a worker) and from
resetting another slot's worktree by hand. Filed P2 (data-coverage gap, small + precisely scoped) so the 4-league
coverage survives regardless of what happens to slot-9's dead worktree. This is duplicate-work fallout, not a data-
correctness defect in landed data. Cross-flagged to review (agt-c83ba7), who raised the divergence (msg 1964).
