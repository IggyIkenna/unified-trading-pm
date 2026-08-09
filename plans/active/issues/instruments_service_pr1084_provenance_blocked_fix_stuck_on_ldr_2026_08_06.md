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
asset_group:
  [sports, ci] # corrected 2026-08-08 (/ag-closeout-audit ao) -- was [sports, ao]. Content is 100% CI/CD
  # promotion-pipeline governance (provenance gate, quickmerge-bypass, promotion-blocked PR) -- nothing touches
  # agent-orchestrator dispatch/worker-lifecycle/framework tooling, the domains the `ao` tranche covers. Per
  # doc-frontmatter-schema.md §5, `ao` and `ci` are distinct sibling enum values split 2026-07-27 specifically to
  # separate these two concerns.
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [provenance-gate, quickmerge-bypass, dp-catalog-001, promotion-blocked, instruments-service, ci-governance]
related:
  [
    /plans/active/issues/sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md,
    /plans/active/issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md,
    /plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-08-06
last_updated: "2026-08-08"
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
  [
    /plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md,
    /plans/active/issues/sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
---

> **✅ RESOLVED 2026-08-08 — verified against live GitHub, not inferred. This doc's blocker has CLEARED.** The open todo
> asks whether to bulk-bless the ~19 foreign commits or patch the promotion gate's ancestry check. **Neither is needed —
> a promotion has since succeeded.** Measured 2026-08-08: `IggyIkenna/instruments-service` `main` HEAD is `db7f7d3b44`
> _"chore(promote): LDR → main (Option-B direct)"_ dated **2026-08-07T23:02:53Z**, with the back-merge to
> `live-defi-rollout` landing at 23:03:05Z. PR #1084 itself remains CLOSED (never merged), but a later promote carried
> the work through. **The dependent sports fix is confirmed deployed**:
> `origin/main:scripts/build_instrument_catalogue.py` contains `junk_name_skips`, the observability hook shipped with
> the DP-CATALOG-001 fix. NOTE that SHA-based ancestry checks against the pre-rewrite `instruments-service@497c4f5e` are
> unreliable here — that repo underwent a history rewrite (`.stale-pre-history-rewrite-20260805T112453Z`), so the fix
> was verified **by content**, not by SHA reachability.

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

- [x] [DATA] P1. ✅ RECONCILED (2026-08-06, follow-up session) — read both diffs in full. `8ae53f7a` (2026-06-27,
      already on `main`) adds `reject_junk_instruments()` to `instruments_service/engine/orchestrator/venue_core.py`,
      wired into `_filter_and_enrich_records()` in `process_fetch.py` — a CAPTURE-TIME guard on trading-instrument
      records (checks `base_asset`/`raw_symbol`/ `instrument_key` for non-ASCII or known test-bases) for the
      CEFI/DEFI/TradFi venue-capture pipeline. `497c4f5e` (2026-08-06) instead wraps `build_team_id`/`build_player_id`
      calls in `scripts/build_instrument_catalogue.py`'s `build_sports_fixture_team_player_catalogue()` in try/except —
      a CATALOGUE-BUILD-TIME safety net reading sports fixture/team/player display names already sitting in
      `sports_reference/by_date/` parquets (via `_iter_sports_ftp_snapshots`), a completely different data domain
      (sports reference data, not `InstrumentRecord`s) that never passes through `reject_junk_instruments()` at all
      (confirmed: `reject_junk_instruments` has exactly one call site, `process_fetch.py:358`, nowhere near the sports
      FTP snapshot/catalogue code path). **Verdict: NOT redundant, NOT superseded** — different bugs, different
      pipelines, both legitimate and independently necessary. `497c4f5e` does NOT get reverted.
- [x] [DATA] P1. ✅ `497c4f5e` needs NO re-ship — it already carries a proper `Quickmerge: agent` trailer
      (`git show 497c4f5e` confirms it) and `check_strict_quickmerge.py` correctly classifies it as
      `passed through     quickmerge` (not a violation). PR #1084's closure was NOT caused by `497c4f5e`'s own
      provenance — see the BLOCKED-OPERATOR todo below for the real cause.
- [x] ✅ [CI] P1. **STALE-CHECK CLOSE 2026-08-09** — superseded by this doc's own 2026-08-08 `✅ RESOLVED` banner at the
      top of the file, which is the LATEST edit to this doc (commit `6860859a`, 2026-08-08T04:05:30+01:00) — it postdates
      the `na-eligibility-audit 2026-08-08` entry below (commit `a86c8e1d`, 2026-08-08T02:40:14Z) that still called this
      blocked, so the banner is the current, correct verdict, not the audit entry. Independently re-verified live
      2026-08-09: `db7f7d3b` ("chore(promote): LDR → main (Option-B direct)", 2026-08-07T23:02:53Z) is on
      `origin/main`, and `origin/main:scripts/build_instrument_catalogue.py` contains `junk_name_skips` — the
      DP-CATALOG-001 fix this todo was waiting on IS live on main today, via a later promote (Option-B direct) that
      carried the work through even though PR #1084 itself never merged. **UPDATED 2026-08-06 — root-cause fix already
      shipped (`unified-trading-pm@7b5390649`), but
      instruments-service specifically still needs a second, separate step.** `[CI]` tag (was `[BLOCKED-OPERATOR]`) —
      `commit_reachable()`'s ancestry check is hardened and live; the marker-corruption bug itself is fixed fleet-wide.
      But per `provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`'s own follow-up finding, the
      now-CORRECT range computation exposes that instruments-service's real range is a genuine ~19-commit foreign,
      multi-subsystem list — this was never a marker-bug artifact, it's real un-promoted work needing either the owning
      agents to re-ship their own commits or an operator-authorized `reprovenance_bypass.sh` sweep (per the
      `utl_ldr_main_blocked_34_foreign_quickmerge_bypasses_2026_07_21.md` precedent) — a judgment call not resolved by
      this ruling. Re-verify (a)/(b)/(c) below once THAT second step lands, not just the marker-bug fix. **Cannot verify
      the promotion PR merges to main or the deployed image freshness** — the actual blocker is a much larger,
      newly-discovered, cross-repo issue: the LDR→main provenance-marker computation is corrupted for
      instruments-service (and 2 other repos) by the 2026-08-05T11:24:53Z security-driven git history rewrite, producing
      a false-positive-flooded ~3,701-commit provenance range instead of the real ~19-commit one. Full finding +
      evidence + remedy options:
      `/plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`. Not fixable
      within this session's scope (foreign bulk-bless / gate-code-change both need an operator call per the
      `utl_ldr_main_blocked_34_foreign_quickmerge_bypasses_2026_07_21.md` precedent). Once that doc's remedy lands and
      instruments-service gets one clean promote through, re-verify: (a) the promotion PR merges to main carrying
      `497c4f5e`, (b) the deployed `:latest` Cloud Run image digest actually changes, (c) a manual
      `gcloud run jobs execute lifecycle-catalogue-regen-sports --wait` re-trigger proves a clean run from the new
      image.
- [x] [DATA] P3. ✅ Reconciled — `8ae53f7a` is NOT the same follow-up as this issue's sibling doc's P3 todo ("trace the
      upstream encoding defect... most likely an MTDS api_football lineups adapter"). `8ae53f7a` only guards the
      CEFI/DEFI/TradFi venue-capture path (`base_asset`/`raw_symbol`/`instrument_key` on `InstrumentRecord`s) — it has
      no bearing on sports fixture/team/player display-name capture at all, and does not touch the api_football lineups
      adapter. The sibling doc's P3 (tracing the actual upstream mojibake-encoding source for sports names) remains
      fully open and un-addressed by either commit reconciled here — `497c4f5e` only stops it from crashing the
      catalogue rollup, it does not fix the root-cause encoding defect. No redundant todo to close.

## Catalogue freshness re-verified (2026-08-06, follow-up session)

`gsutil stat gs://instruments-store-sports-prd-central-element-323112/prod/catalog.parquet` still shows
`Update time: Thu, 06 Aug 2026 08:37:26 GMT` (unchanged) — as of 13:15 UTC that is ~4.6h old, still well within the 24h
DP-CATALOG-001 budget. Not an active incident; the `lifecycle-catalogue-regen-sports` cron's next 01:00 UTC run is the
real forward-looking risk window, unchanged from the original assessment.

## Progress Log

- **main-session, 2026-08-06**: Found while re-checking DP-CATALOG-001/PR #1084 status after a GitHub API rate limit
  cleared. PR #1084 closed (not merged) by the provenance gate; live-verified both `497c4f5e` and `8ae53f7a` are on LDR
  but neither is on main. Catalogue is currently healthy (refreshed 08:37 UTC today) so this is filed as a
  forward-looking P1, not an active page. Did not attempt to reconcile/re-ship the fix myself in this session —
  determining whether `8ae53f7a` supersedes `497c4f5e` needs a real diff read, and re-shipping someone else's fix via
  quickmerge on their behalf carries enough risk that it belongs to a dedicated follow-up rather than a rushed
  side-action.
- **/plan-reconcile ao, 2026-08-06**: Corrected the ancestry facts — `8ae53f7a` is on `main` (since 2026-06-27), only
  `497c4f5e` is stuck. Diff-overlap read still not done at that point.
- **follow-up session, 2026-08-06**: Reconciled both commits by reading full diffs (see todos above) — different
  pipelines (trading-instrument capture-time guard vs. sports catalogue-build-time safety net), not redundant,
  `497c4f5e` still needed and already correctly quickmerge-provenanced (no re-ship needed). Re-checked catalogue
  freshness: still healthy (unchanged 08:37 UTC snapshot, ~4.6h old at 13:15 UTC check). Investigating why PR #1084 was
  actually blocked (since `497c4f5e` itself is clean) surfaced a much bigger, unrelated, cross-repo finding: the
  promote-provenance-marker mechanism is corrupted post-history-rewrite for 3 repos (instruments-service,
  unified-trading-library, market-data-processing-service), producing a false-positive-flooded provenance range that
  structurally blocks ANY promote PR for these repos right now, independent of what content it carries. Filed as a
  dedicated new issue doc
  (`/plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`) rather than
  attempting an autonomous fix — both remedy paths (bulk-bless the real 19 foreign bypasses, or patch the marker's
  ancestry check) are judgment calls with fleet-wide blast radius that the established precedent
  (`utl_ldr_main_blocked_34_foreign_quickmerge_bypasses_2026_07_21.md`) says belong to an operator decision, not an
  autonomous sub-task fix. This issue's promotion-verification todo is therefore BLOCKED-OPERATOR pending that doc's
  resolution, not something this session could close out.
- **context-scout 2026-08-07**: refreshed context_scope (3 entries) — added
  `provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`, which the still-open `[CI] P1` todo
  names directly as carrying "Full finding + evidence + remedy options" for the actual current blocker (the marker-bug
  fix already shipped fleet-wide, but instruments-service's real ~19-commit foreign range still needs that doc's own
  remedy); the 2 pre-existing entries re-verified, still resolve.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — the fleet-wide marker-bug fix already shipped;
  instruments-service's own ~19-commit foreign range still needs this doc's own remedy, dependency-blocked.
- **na-eligibility-audit 2026-08-08**: re-read (in scope again — the only change since the 08-07 marker was
  `/ag-closeout-audit ao`'s `asset_group` correction, `[sports, ao] → [sports, ci]`; no content/scope change).
  **KEEP-NA, valid — verdict UNCHANGED.** Re-verified live: `497c4f5e` still not an ancestor of `origin/main`; the
  blocking doc (`provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`) is still `status: open`,
  unlocked. The 1 open `[CI] P1` todo is DEPENDENCY_BLOCKED on that doc's own operator-gated remedy — not a clean
  worker-determinable outcome today.
- **stale-check-sports 2026-08-09**: this "still blocked" verdict above was itself already stale at write time — this
  doc's own `✅ RESOLVED 2026-08-08` banner at the top of the file (commit `6860859a`, 2026-08-08T04:05:30+01:00)
  postdates this very audit entry (commit `a86c8e1d`, 2026-08-08T02:40:14Z) and supersedes it: a later LDR→main promote
  (`db7f7d3b`, 2026-08-07T23:02:53Z, Option-B direct) carried the DP-CATALOG-001 fix through even though PR #1084 itself
  never merged. Independently re-verified live 2026-08-09: `db7f7d3b` is on `origin/main`, and
  `origin/main:scripts/build_instrument_catalogue.py` contains `junk_name_skips`. Closed the last open `[CI] P1` todo
  citing this. **All todos in this doc are now `[x]` — this doc is an ARCHIVE candidate** (not archived this pass —
  archival requires the 6-step referrer-fixup ritual, out of scope for a staleness-only sweep; `status:` frontmatter left
  at `open` rather than `resolved` since `check_terminal_status_archived` hard-fails an unarchived `resolved` doc at
  commit time — a future archival pass should flip both together).
