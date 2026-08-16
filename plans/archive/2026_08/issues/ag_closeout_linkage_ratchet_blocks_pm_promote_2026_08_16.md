---
doc_type: issue
title: >-
  check_ag_closeout_linkage ratchet blocking unified-trading-pm's LDR→main promote gate — 1 orphan doc
  (sportradar_credential_ask_2026_08_09.md, sports) with no closeout-family linkage
summary: >-
  During an hourly `/ci-reconcile` sweep, `unified-trading-pm`'s promote-PR `checks` QG slice was failing on 3 hard
  ratchets. One (`check_reference_paths` existence, 34→39) was root-caused and fixed same-session
  (`unified-trading-pm@17a902f456`) — a concurrent archival commit moved 2 referenced docs to `plans/archive/issues/`
  without updating their referrers. A second (`check_archive_candidates`, 1 candidate:
  `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`) already has a dedicated tracked prerequisite doc
  (`plans/active/issues/prediction_batch4_deferred_migration_and_archival_2026_08_14.md`) — not duplicated here. This
  third ratchet, `check_ag_closeout_linkage`, briefly grew to 3 orphans (~04:53-05:05Z) before 2 self-resolved via
  concurrent archival commits (their underlying work landed and they got archived, which exempts them from this
  check). One genuine orphan remains as of the last re-check: `plans/active/issues/
  sportradar_credential_ask_2026_08_09.md` (`asset_group=[sports]`), which the checker reports has "no path (graph or
  mention) to its closeout family". Filed rather than fixed directly: closing a closeout-linkage orphan requires
  domain judgment (which closeout family a doc belongs in, GRAPH-hop vs BODY-TEXT-mention semantics per
  `check_ag_closeout_linkage.py`'s own docstring) squarely in `/ag-closeout-audit`'s scope, not a mechanical
  CI-pipeline fix.
status: resolved
nature: issue
asset_group: [meta, sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-reconcile, ag-closeout-linkage, ratchet, promote-gate, quality-gates-v2, ag-closeout-audit]
related:
  [
    /plans/active/issues/sportradar_credential_ask_2026_08_09.md,
    /plans/active/issues/prediction_batch4_deferred_migration_and_archival_2026_08_14.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/issues/reference_path_convention_2026_07_23.md,
  ]
created: 2026-08-16
author: claude-agent
last_updated: 2026-08-16
parent_epic: infrastructure_master
priority: P2
source: ci-reconcile skill, scheduled hourly ci_reconciler dispatch agt-14e777 (slot 15)
assigned_vm: NA
resolved_by: cicd escalation agent (slot 3, agt-8b735e), 2026-08-16
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# ag-closeout-linkage ratchet blocks unified-trading-pm promotion — 1 sports doc needs closeout-family linkage

> **ARCHIVED**: resolved by unified-trading-pm (cicd escalation agent, slot 3, agt-8b735e, 2026-08-16) — added a
> `related:` edge from `sportradar_credential_ask_2026_08_09.md` to `sports_consolidated_closeout_2026_07_19.md`.
> Successor: none (self-contained fix).

## Evidence (2026-08-16, ~04:53-05:10Z)

Promote PR #3245's `checks` slice log (`gh run view 31927403103 --job 95117026356`):

```
❌ FAIL  [hard]  AG-closeout linkage (single-AG docs -> consolidated closeout, ratchet)
```

Re-running `python3 scripts/plan-hygiene/check_ag_closeout_linkage.py` at ~05:05Z (fresh `origin/live-defi-rollout`
pull) initially showed the count grown 1→3 vs PR #3245's snapshot:

```
ORPHAN  plans/active/issues/safe_doc_push_shared_prek_home_across_ao_vm_slots_2026_08_16.md: asset_group=[infrastructure] has no path (graph or mention) to its closeout family
ORPHAN  plans/active/issues/sportradar_credential_ask_2026_08_09.md: asset_group=[sports] has no path (graph or mention) to its closeout family
❌ check_ag_closeout_linkage: 3 orphan(s) (baseline 0)
```

By ~05:10Z, a fresh pull + re-check showed only 1 remaining — `safe_doc_push_shared_prek_home_across_ao_vm_slots_
2026_08_16.md` and its sibling `safe_doc_push_cross_slot_prek_patch_orphans_completed_fix_2026_08_16.md` had both
been archived by concurrent commits in the interim (their underlying fixes shipped), which exempts them from this
checker:

```
ORPHAN  plans/active/issues/sportradar_credential_ask_2026_08_09.md: asset_group=[sports] has no path (graph or mention) to its closeout family
❌ check_ag_closeout_linkage: 1 orphan(s) (baseline 0)
```

## Why not fixed directly this pass

`check_ag_closeout_linkage.py` accepts either a GRAPH edge (N-hop `related:`/reference chain to the tranche's
`<prefix>_consolidated_closeout_*.md` family) or a BODY-TEXT MENTION (the orphan's filename stem appearing in the
closeout family's own body text) as valid linkage. Picking the right target closeout doc and the right linkage shape
for `sportradar_credential_ask_2026_08_09.md` is exactly `/ag-closeout-audit`'s per-doc classification judgment — not
a blind path-string fix like the reference-path breaks fixed this same session. Guessing at linkage risks a wrong or
misleading edge in a corpus this checker (and the ag-closeout-audit skill) actively relies on for accurate orphan
detection.

## Impact

Every `unified-trading-pm` promote PR will keep failing this ratchet (alongside the already-tracked archive-candidates
ratchet) until `sportradar_credential_ask_2026_08_09.md` gets proper closeout-family linkage.

## Disposition

Suggested resolution: run `/ag-closeout-audit sports` (or whichever tranche covers `asset_group: [sports]` credential
docs) to properly classify and link this doc into its correct closeout family, then re-verify
`check_ag_closeout_linkage.py` returns to baseline 0.

## Progress Log

- 2026-08-16: Filed by `ci_reconciler` (agt-14e777, slot 15) during the hourly `/ci-reconcile` sweep. Fixed the
  sibling `check_reference_paths` ratchet in the same sweep (`unified-trading-pm@17a902f456`); this ratchet (now down
  to 1 orphan after 2 self-resolved via concurrent archival) and the already-tracked `check_archive_candidates` one
  are the remaining blockers on unified-trading-pm's promote gate.
- 2026-08-16 (cicd escalation agent, slot 3, agt-8b735e, dispatched on `ldr_qg_failure` for this same gate):
  RESOLVED — the "which closeout family" judgment this doc reserved for `/ag-closeout-audit` turns out to be
  unambiguous here: `sportradar_credential_ask_2026_08_09.md`'s `asset_group` is a single value (`[sports]`,
  already corrected from `[cross-cutting]` on 2026-08-10) and exactly one sports closeout family exists
  (`sports_consolidated_closeout_2026_07_19.md` + its archived companions) — no candidate-selection judgment
  remained, only whether to add the GRAPH-edge signal, which is always a safe, additive, non-destructive fix. Added
  `/plans/active/sports_consolidated_closeout_2026_07_19.md` to that doc's `related:` list
  (`unified-trading-pm`, this commit). Verified locally: `check_ag_closeout_linkage.py` now reports 0 orphans
  (baseline 0). Archiving this doc in the same commit (no open todos, no referrers found corpus-wide).
