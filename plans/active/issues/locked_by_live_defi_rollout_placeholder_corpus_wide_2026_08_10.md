---
doc_type: issue
title: "locked_by: live-defi-rollout is a hardcoded placeholder, not a real lock claim — 96 docs corpus-wide"
summary: >-
  `locked_by: live-defi-rollout` (the BRANCH name, not any actor/agent/operator identity) is stamped on 96 plans/active
  + plans/active/issues docs. Traced to a hardcoded default in scripts/plans/fix_epic_frontmatter_2026_05_21.py:133.
  Genuine locks in this corpus carry a real actor id (`plan_reconciler (agt-xxxxxx) since <ts>`); this value never has.
  Blocks archival on at least 1 confirmed fully-done ui-tranche doc (locked_since predates the doc's own created date by
  2 months — logically impossible for a real claim), flagged 5 consecutive audit passes with zero resolution because
  `locked_by:` is a HARD-STOP auto-unlock is never autonomous. Discovered during the 2026-08-10 ui-tranche
  plan_reconciler run; filed corpus-wide since the fix (if ruled a bug) touches docs across every tranche, not just ui.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [locked_by, archival, hygiene, corpus-wide, plan_reconciler, bug]
related:
  [
    /plans/archive/2026_08/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md,
    /plans/active/issues/plan_reconciler_findings_ui_2026_08_10.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role:
drift_direction: none
locked_by:
locked_since:
resolved_by:
source:
  "plan_reconciler dispatch agt-ec1688 (ui tranche, 2026-08-10) — discovered while investigating a stuck ui archive
  candidate"
depends_on: []
---

# `locked_by: live-defi-rollout` — hardcoded placeholder, not a real lock (96 docs corpus-wide)

## Evidence

1. **`live-defi-rollout` is the shared branch name**, not any registered actor. Every OTHER `locked_by` value in the
   corpus is a real identity: `plan_reconciler` (8×), `plan_reconciler (agt-XXXXXX) since <ISO ts>` (multiple,
   dispatch-id-bearing), `harsh-fleet-audit` (2×). `live-defi-rollout` is by far the most common non-empty value (96
   occurrences vs. single/low-double-digits for every real actor).
2. **Root cause located**: `scripts/plans/fix_epic_frontmatter_2026_05_21.py:133` —
   `lines.append("locked_by: live-defi-rollout")` — a one-off epic-frontmatter-conformity script (its own header:
   `Lifecycle: oneoff`, `Delete-when: after prod-run + orphan-sweep=0`) hardcodes this literal string as part of the
   canonical frontmatter it writes. That script's own target is `plans/epics/`, so it is not the direct writer for the
   96 `plans/active`/`plans/active/issues` hits below — but the exact string, and the exact date, match too closely to
   be coincidence; a sibling doc-creation template most likely copied the same placeholder pattern.
3. **`locked_since` distribution** (92 docs with a non-empty `locked_since`, of the 96): 35 read exactly `2026-05-21`
   (the fix-script's own date), 33 are BLANK (locked_by set, locked_since empty — another non-genuine-lock tell), the
   remaining 24 are spread `2026-05-25`→`2026-07-11` (consistent with a copy-pasted template default that kept
   propagating into newly-created docs over months, each stamped with that doc's own creation time rather than a real
   claim event).
4. **Directly blocked a confirmed-done archive** (RESOLVED 2026-08-10 for this one doc, see Progress Log — the
   corpus-wide question below is unchanged):
   `/plans/archive/2026_08/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` —
   `locked_by: live-defi-rollout`, `locked_since: 2026-05-21`, but `created: "2026-07-21"` — the lock predated the doc's
   own existence by 2 months, which is impossible for a genuine claim. All 3 todos were `[x]` done (re-verified
   2026-08-10). Flagged as a likely-stale lock on **5 consecutive audit passes**
   (`ui_satellite_ao_dispatch_batch1_2026_08_06.md` § Findings; `plan_reconciler_findings_2026_08_07.md`;
   `ag_closeout_audit_ui_parked_2026_08_08.md`; `ag_closeout_audit_ui_parked_2026_08_09.md`; this run) with zero
   autonomous resolution (unlocking is a HARD-STOP no worker may do regardless of confidence) — the operator was then
   asked directly, approved the `[unlock-plan]` for this specific doc, and it was unlocked + archived 2026-08-10.

## Why this is filed corpus-wide, not folded into the ui-tranche findings doc

The evidence above is ui-specific (1 doc), but the underlying value appears on 96 docs across (at minimum) every tranche
that had active docs around 2026-05-21→2026-07-11 — a ui-scoped run cannot see the other 95, and a fix (if ruled a bug)
would touch docs this run has no mandate to write. Filed here per the "outside every plan → issue doc"

- "big finding … cross-repo" triage rule so a future `all`-scoped `/plan-reconcile` run (or a dedicated remediation
  plan) can pick it up with full corpus visibility.

## Recommendation

**[WORKER REC] Option A** — treat `locked_by: live-defi-rollout` as categorically non-genuine (it is never a real actor
name) and permit `/plan-reconcile`/`/ag-closeout-audit` to archive a doc carrying it, PROVIDED every other
archive-eligibility check independently passes (all todos `[x]` HARD-verified, unlocked-in-every-other-respect,
non-grace) — i.e. treat this one specific value as equivalent to no lock, rather than as a human/agent claim.

**Option B** — leave the HARD-STOP as-is (any non-empty `locked_by` blocks auto-archival, no exceptions) and instead run
a one-time corpus-wide sweep that CLEARS `locked_by`/`locked_since` on every doc where the value is exactly
`live-defi-rollout` (restoring them to the pre-bug state), after which normal archival logic picks them up on the next
pass. This fixes the root cause instead of special-casing the auto-fixer.

**Option C** — leave every doc as-is; require a human to manually confirm+clear each of the 96 one at a time.

Option B is the cleanest (fixes the actual data defect once, doesn't change any skill's unlock policy, doesn't risk
mis-treating a doc that coincidentally has a real reason to be locked under that same string). Not applied autonomously
— clearing `locked_by` is itself an unlock action, HARD-STOP, operator-only.

## Todos

- [ ] [OPERATOR] P1. Rule which option (A/B/C) above applies, or a different fix.
- [ ] [SCRIPT] P2. Once ruled: if Option B, write a small one-off script (`scripts/plans/` + `# Lifecycle: oneoff` +
      `# Delete-when:` marker per script-homes.md) that clears `locked_by`/`locked_since` on exactly the docs where
      `locked_by == "live-defi-rollout"` (verify each doc individually — do not blind-regex the whole corpus in one
      shot), commit in batches, re-run `check_archive_candidates.sh` after.
- [x] ✅ [REVIEW] P2. Once unlocked, re-run archival eligibility on
      `plans/active/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` specifically (all 3 todos
      already HARD-verified done as of 2026-08-10) and archive via the 6-step ritual if still eligible.
      **RESOLVED 2026-08-10** — this specific doc did not wait on the corpus-wide Option A/B/C ruling (todos 1-2 above,
      still open): the operator was asked directly and explicitly approved a targeted `[unlock-plan]` for just this one
      doc. All 3 todos re-verified `[x]` done, `locked_by`/`locked_since` cleared, archived to
      `/plans/archive/2026_08/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` via the 6-step
      ritual, all active-corpus referrer paths fixed. The remaining 95 docs carrying the same placeholder value are
      unaffected — todos 1-2 stay open for that corpus-wide decision.

## Progress Log

- **2026-08-10** — Filed by plan_reconciler (ui-tranche dispatch `agt-ec1688`) while investigating why
  `deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` has survived 5 archive-eligible flags with zero
  action. Root-caused to `scripts/plans/fix_epic_frontmatter_2026_05_21.py:133` + corpus-wide grep evidence (96 docs,
  distributional analysis above). Not fixed — corpus-wide fix is outside this run's ui-scoped mandate and unlocking is
  HARD-STOP operator-only regardless of scope.
- **2026-08-10 (later same day)** — Operator asked directly whether to unlock+archive
  `deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` specifically, and approved. Flipped todo 3 above
  citing that approval; todos 1-2 (the corpus-wide Option A/B/C ruling for the remaining 95 docs) remain open — this was
  a targeted single-doc exception, not a resolution of the underlying corpus-wide question.
