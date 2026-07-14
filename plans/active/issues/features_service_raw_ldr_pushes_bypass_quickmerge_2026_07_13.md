---
doc_type: issue
title: features-service — three raw pushes to live-defi-rollout bypassed quickmerge, blocking LDR->main auto-merge
summary: |
  Surfaced while resolving cicd escalation agt-e94007 (features-service quality-gates-v2 RED on main). Diagnosed as
  PROMOTION STUCK: fleet promote PR #751 had a trivial uv.lock version-drift merge conflict (resolved) plus a
  quality-gates-v2 never-reported deadlock on the PR head (re-triggered). Once both were cleared, the fleet bot's
  `promote_provenance_range.py` gate (fixed today per promote_provenance_marker_stale_head_query_2026_07_13.md) still
  correctly refuses to arm auto-merge: three commits landed on live-defi-rollout within the resolved provenance range
  (6cfe2abf..HEAD) with no `Quickmerge:` trailer — a genuine bypass, not the stale-marker false positive the other doc
  covers. All three commits carry `Co-Authored-By: Claude Sonnet 5` and slot-tagged author identities (slot-10,
  slot-5), i.e. agent sessions raw-pushed rather than shipping via `quickmerge.sh --agent`. Operator ruling (via
  BLK-163a306c on this escalation): leave PR #751 unarmed — this is the gate working as intended, not a bug to route
  around; file this doc so remediation is tracked rather than left implicit in the blocked-question thread.
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [features-service]
scope: [engineer, admin]
tags: [cicd, provenance-gate, quickmerge, ldr-to-main, raw-push]
related:
  [
    promote_provenance_marker_stale_head_query_2026_07_13.md,
    features_sports_unbounded_memory_early_history_dates_2026_07_13.md,
    ../../codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-13
last_updated: 2026-07-14
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.5
assigned_role: cicd
drift_direction: advance-code
source: [features-service@588eed0e4848, features-service@a9684e27da96, features-service@208516e6aa69]
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
  "verification 2026-07-14 (slot 5, this doc) — no new provenance violations landed after the 3 flagged commits. PR #751
  merged 2026-07-13T22:33:59Z (mergedBy IggyIkenna); its successor #752 (created immediately after, same provenance
  range check) merged cleanly 2026-07-13T23:47:55Z with no further bypass commits blocking it. The one intervening
  direct push (features-service@8ecce951, cloudbuild.yaml sha-tag-guard) is a documented dirty-deps carve-out, not a
  violation, and the gate accepted it. Confirmed on the live fleet-promote run (unified-trading-pm run 29325493501,
  2026-07-14T10:29Z): 'TIER A PASS features-service: ci_status=MAIN_GREEN' / 'SKIP features-service: main tree == LDR
  tree (content-identical...)' / 'provenance: promote-range is quickmerge-clean (or carve-outs only)' — main is fully
  caught up with LDR, provenance clean. Todo 2 satisfied; no auto-merge blockage remains for features-service. Note: the
  OOM investigation this doc gated on (features_sports_unbounded_memory_early_history_dates_2026_07_13.md) has NOT
  itself concluded (still status: open, active P0 root-cause work on compute_shot_quality_batch) — but the concrete
  thing this todo asked to verify (clean auto-merge, no further provenance violations) already happened independently
  and holds as of this check, so there is nothing further blocking on the promote side."
---

# features-service — raw LDR pushes bypassing quickmerge block LDR->main auto-merge

## What I found

Resolving cicd escalation `agt-e94007` (features-service `quality-gates-v2` RED on `main`), I found the actual wall was
PROMOTION STUCK on fleet promote PR #751 (`promote/features-service/588eed0e4848` -> `main`):

1. A trivial `uv.lock` merge conflict (`click` specifier `>=8.3.2` on `main` vs `>=8.3.3` on the LDR-derived promote
   branch — both `pyproject.toml` files already agreed on `>=8.3.3`; `main`'s lockfile metadata was simply one
   version-bump cycle behind). Resolved on the merits (LDR's newer value), pushed to the promote branch — no work
   dropped.
2. `quality-gates-v2` had never fired on the PR head at all (a never-reported-check deadlock). Re-triggered via
   `gh workflow run quality-gates-v2.yml --ref promote/features-service/588eed0e4848`.

With both cleared, the fleet bot's `promote_provenance_range.py` gate (marker-resolution bug fixed earlier today,
`unified-trading-pm@20db96085`) still refuses to arm auto-merge:

```
⛔ provenance: features-service has non-quickmerge CODE on LDR — NOT arming auto-merge (PR left open)
promote-provenance-range[features-service→main]: mode=marker marker=6cfe2abf28e9 → 6cfe2abf28e9..origin/live-defi-rollout
```

The resolved marker (`6cfe2abf`, 2026-07-13T17:46:08Z) is recent/narrow — confirming the earlier marker-query fix is
live and this is NOT the stale-marker false-positive that `promote_provenance_marker_stale_head_query_2026_07_13.md`
documents. `check_strict_quickmerge.py` over the range flags three real commits with no `Quickmerge:` trailer:

| SHA        | Time (UTC)           | Author (slot)                    | Subject                                                                                         |
| ---------- | -------------------- | -------------------------------- | ----------------------------------------------------------------------------------------------- |
| `208516e6` | 2026-07-13T18:38:13Z | ikennaigboaka [slot-5·planning]  | fix(volatility): resolve io/writer.py bucket via resolve_bucket_name SSOT                       |
| `a9684e27` | 2026-07-13T20:31:40Z | ikennaigboaka [slot-5·planning]  | fix(sports): stop venue_id collapsing to "" in read_venues/normalize_fixtures/travel_calculator |
| `588eed0e` | 2026-07-13T20:56:54Z | ikennaigboaka [slot-10·planning] | chore(sports): add full-pipeline + multi-date-loop OOM profiling harnesses                      |

All three carry `Co-Authored-By: Claude Sonnet 5` — agent sessions pushed directly to `live-defi-rollout` instead of via
`bash scripts/quickmerge.sh "<msg>" --agent --files '<paths>'`, in violation of CLAUDE.md's "CODE reaches the
integration branch ONLY via quickmerge" HARD RULE. The `588eed0e` commit is explicitly tied to
`plans/active/features_sports_unbounded_memory_early_history_dates_2026_07_13.md` (an active OOM-investigation plan),
suggesting the raw pushes came from that plan's working sessions on slot-5/slot-10, not a one-off mistake.

## Why it matters

- The fleet promote gate is working AS DESIGNED — it is correctly holding `main` back from code that skipped the
  quickmerge quality-gate boundary. Overriding it would defeat the entire purpose of the HARD RULE.
- `main` stays behind LDR for `features-service` until this clears — low urgency today (no other main-blocking work is
  queued behind it per this escalation), but the same failure mode will recur on every subsequent promote cycle until
  the bypassing commits are properly re-shipped or the pattern stops.
- If slot-5/slot-10 sessions are routinely raw-pushing during OOM-investigation work (harness scripts, hot-fixes found
  mid-investigation), that's a process gap worth closing at the source, not just at the promote gate.

## Recommended decision

Per operator ruling on BLK-163a306c (this escalation): **leave PR #751 open/unarmed** — do not force-merge. Matches the
documented precedent for genuine (non-false-positive) quickmerge bypasses in
`promote_provenance_marker_stale_head_query_2026_07_13.md`'s fleet-wide audit results (6 other repos, same "no forced
merge, hold until re-shipped or reverted" resolution).

## Todos

- [x] ✅ [SCRIPT] P2. Confirm whether the `features_sports_unbounded_memory_early_history_dates_2026_07_13.md` plan is
      still active on slot-5/slot-10; if so, remind those sessions (or their next `/boot`) to ship any further findings
      via `quickmerge --agent`, not raw `git push`. (repo: unified-trading-pm) — **CONFIRMED STILL ACTIVE, slot 11,
      2026-07-14**: `features_sports_unbounded_memory_early_history_dates_2026_07_13.md` is `status: open`,
      `last_updated: 2026-07-13`, with dense same-day activity from many slots (4, 5, 6, 7, 8, 9, 10, 12, 14) — the OOM
      investigation itself is now essentially concluded (root cause pinned to `venue_id` collapsing to `""` causing a
      cartesian-product merge explosion; fixed `features-service@a9684e27`/`c3e3ebfe`; all 3 poison dates verified clean
      on the real VM fleet by slot 9). Left an explicit reminder note directly in that plan's own Progress Log (see its
      "Reminder — ship via quickmerge, not raw git push" entry) rather than relying on a per-slot boot message this
      dispatch can't directly send — every future session reading that plan (the `sequential: true` + heavy per-touch
      convention this doc already follows) will see it before its next commit.
- [x] ✅ [SCRIPT] P3. Once the `features_sports_unbounded_memory_early_history_dates_2026_07_13.md` investigation
      concludes, verify PR #751 (or its successor per-SHA-ref PR) auto-merges cleanly on the next fleet drain with no
      further provenance violations in range. (repo: features-service) — **VERIFIED, slot 5, 2026-07-14**: PR #751
      merged 2026-07-13T22:33:59Z; successor #752 merged cleanly 2026-07-13T23:47:55Z with no further provenance
      violations. Latest fleet-promote run (unified-trading-pm run 29325493501, 2026-07-14T10:29Z) confirms
      features-service main tree == LDR tree, provenance clean. See `resolved_by` frontmatter for full evidence. The
      gating OOM investigation had not itself formally concluded (still `status: open`) but the concrete auto-merge
      behavior this todo asked to verify already held independently — see note in `resolved_by`.
