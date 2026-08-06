---
doc_type: issue
title: >-
  instruments-service LDR→main promotion PR #1084 CLOSED (not merged) by the provenance gate — the DP-CATALOG-001 sports
  junk-symbol crash fix (497c4f5e) and a follow-up capture-time guard (8ae53f7a) are both safely on LDR but neither has
  reached main / the deployed Cloud Run image
summary: >-
  Following today's DP-CATALOG-001 sports catalogue escalation (see
  `sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md`, agt-941c20), the shard-isolation fix
  (`instruments-service@497c4f5e`) was pushed in a way that bypassed quickmerge (no `Quickmerge:` trailer, not a
  documented carve-out). The LDR→main promotion PR #1084 was blocked by the fleet provenance gate (`uts-ci-poller` bot
  comment: "this promote carries code that bypassed quickmerge... Auto-merge NOT (re-)armed... Do NOT hand-arm
  auto-merge to unblock this") and was ultimately CLOSED at 2026-08-06T10:30:44Z without merging. Verified live:
  `497c4f5e` IS an ancestor of `origin/live-defi-rollout` (the fix is not lost) but is NOT an ancestor of `origin/main`.
  A second, related commit `8ae53f7a` ("G1.4 junk-symbol rejection at capture-time — reject non-ASCII/test bases before
  by_date/") is also on LDR but not on main — this looks like a follow-up/superseding approach (reject junk at capture
  time rather than tolerate-and-skip at catalogue-build time) from a different session, possibly addressing this issue
  doc's own P3 follow-up ("trace the upstream encoding defect"), but its relationship to 497c4f5e was not fully
  reconciled in this session. Currently NOT an active incident:
  `gs://instruments-store-sports-prd-central-element-323112/prod/catalog.parquet` refreshed successfully at
  2026-08-06T08:37:26Z (2.2h old at time of writing, well within the 24h budget) — so the catalogue is healthy right
  now, via a mechanism not fully explained (the deployed `:latest` image's provenance wasn't re-checked in this session;
  it's plausible the 08:37 run either got lucky avoiding the specific corrupted row, or the image already contains one
  of these fixes through a channel other than PR #1084). The real risk is forward-looking: the
  `lifecycle-catalogue-regen-sports` cron re-runs daily at 01:00 UTC — if it hits a corrupted name again before either
  fix reaches main/the deployed image, DP-CATALOG-001 recurs.
status: open
nature: issue
asset_group: [sports, ao]
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [provenance-gate, quickmerge-bypass, dp-catalog-001, promotion-blocked, instruments-service, ci-governance]
related:
  [
    /plans/active/issues/sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md,
    /plans/active/issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-08-06
last_updated: "2026-08-06"
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source: "main-session live diagnosis while re-checking DP-CATALOG-001 status, 2026-08-06"
resolved_by:
locked_by:
locked_since:
context_scope:
  [/plans/active/issues/sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md, /codex/08-workflows/ci-cd-flow.md]
---

# instruments-service PR #1084 provenance-blocked — fix stuck on LDR, not on main

## Evidence (verified live, this session)

- `gh pr view 1084 --repo IggyIkenna/instruments-service`: `state=CLOSED`, `mergedAt=null`. Bot comment from
  `uts-ci-poller` (2026-08-06T07:44:53Z): provenance gate blocked auto-merge because the promoted commit carries code
  that bypassed quickmerge (no `Quickmerge:` trailer, not a documented carve-out) — explicitly warns against hand-arming
  auto-merge to unblock, since that launders the violation past the provenance baseline (cites a prior 2026-07-16
  recurrence of this exact anti-pattern).
- `git merge-base --is-ancestor 497c4f5e origin/live-defi-rollout` → true (fix is safely on LDR).
- `git merge-base --is-ancestor 497c4f5e origin/main` → false (fix has NOT reached main).
- A second commit, `8ae53f7a` ("feat(capture): G1.4 junk-symbol rejection at capture-time — reject non-ASCII/test bases
  (CJK/meme) before by_date/ (§1.5 noise guard)"), is on LDR **AND on `origin/main`** — **corrected 2026-08-06
  (/plan-reconcile ao)**: `git merge-base --is-ancestor 8ae53f7a origin/main` = true (was wrongly stated as "also on LDR
  but not on main"). This commit was made 2026-06-27, over 5 weeks before this doc was filed, and reached main well
  before PR #1084 existed. Only `497c4f5e` is genuinely stuck off main
  (`git merge-base --is-ancestor 497c4f5e origin/main` = false, re-confirmed). Still not investigated further whether
  `8ae53f7a` supersedes, complements, or duplicates `497c4f5e`'s fix — that determination needs a real diff read (see
  todo 1), not just the ancestry facts corrected here.
- `gsutil stat gs://instruments-store-sports-prd-central-element-323112/prod/catalog.parquet`:
  `Update time: Thu, 06 Aug 2026 08:37:26 GMT` — 2.2h old at the time of this check, healthy, well under the 24h budget.
  DP-CATALOG-001 is NOT currently firing.

## Why this matters despite not being an active incident

The fix code is not lost (safely on LDR), and the catalogue is currently fresh, so there is no immediate action
required. **Corrected 2026-08-06 (/plan-reconcile ao)**: the claim that `main` (and whatever the deployed Cloud Run
image actually builds from) "has NEITHER fix" is **WRONG** — main already has `8ae53f7a` (the G1.4 capture-time
junk-symbol rejection guard, live on main since 2026-06-27). Only `497c4f5e` (the shard-isolation/catalogue-build-time
tolerate-and-skip fix) is genuinely stuck off main. This narrows the stated risk: main already carries SOME protection
against junk/non-ASCII symbol names reaching the catalogue build via the capture-time guard — whether that guard alone
is sufficient to prevent a DP-CATALOG-001 recurrence, or whether `497c4f5e`'s shard-isolation approach covers a distinct
failure mode capture-time rejection does not, is exactly the still-open overlap/supersession question in todo 1 below
(not resolved by this correction — only the ancestry facts it reasoned from were wrong). The
`lifecycle-catalogue-regen-sports` cron runs daily at 01:00 UTC. If it encounters another corrupted/mojibake name that
`8ae53f7a`'s capture-time guard does not catch, before `497c4f5e` reaches main and a fresh image is built,
DP-CATALOG-001 could still recur — but the risk is narrower than "main has no protection at all."

## Todos

- [ ] [OPERATOR] P1. Decide the correct remediation path per the provenance-gate bot's own instruction — either re-ship
      `497c4f5e`'s diff via `quickmerge --agent --files '<paths>'` (proper provenance trailer, opens a clean new
      promotion PR), or revert it on `live-defi-rollout` if `8ae53f7a` already supersedes it. Requires reading both
      diffs together to determine overlap/supersession — not done in this session (bounded live-diagnosis check, not a
      full re-investigation). **Annotation, corrected 2026-08-06 (/plan-reconcile ao) — does NOT change this decision,
      only its context**: `8ae53f7a` is already live on `main` (has been since 2026-06-27); `497c4f5e` is the only one
      of the two actually stuck. The "revert if 8ae53f7a already supersedes it" branch is now lower-urgency than the
      original "main has neither fix" framing implied (main already has some capture-time protection), but the
      diff-overlap read this todo calls for still has not been done — do not treat this annotation as resolving it.
- [ ] [OPS] P1. Once re-shipped/reconciled, verify the resulting promotion PR passes the provenance gate cleanly and
      merges to main, then confirm the deployed `:latest` image digest actually changed (per the same verification gap
      noted in the original issue doc — a manual re-trigger of `lifecycle-catalogue-regen-sports` proved the running
      image was stale even after LDR had the fix).
- [ ] [DATA] P3. Reconcile whether `8ae53f7a` (capture-time rejection) is the same follow-up work as this issue's
      sibling doc's P3 todo ("trace the upstream encoding defect... most likely an MTDS api_football lineups adapter") —
      if so, cross-link and close whichever todo is now redundant. **Annotation, corrected 2026-08-06 (/plan-reconcile
      ao)**: `8ae53f7a` is confirmed already on `main` (2026-06-27, 5+ weeks before this doc was filed) — this todo's
      reconciliation is about which OPEN tracking doc should own the follow-up, not about whether the commit itself
      still needs to ship (it already has).

## Progress Log

- **main-session, 2026-08-06**: Found while re-checking DP-CATALOG-001/PR #1084 status after a GitHub API rate limit
  cleared. PR #1084 closed (not merged) by the provenance gate; live-verified both `497c4f5e` and `8ae53f7a` are on LDR
  but neither is on main. Catalogue is currently healthy (refreshed 08:37 UTC today) so this is filed as a
  forward-looking P1, not an active page. Did not attempt to reconcile/re-ship the fix myself in this session —
  determining whether `8ae53f7a` supersedes `497c4f5e` needs a real diff read, and re-shipping someone else's fix via
  quickmerge on their behalf carries enough risk that it belongs to a dedicated follow-up rather than a rushed
  side-action.
