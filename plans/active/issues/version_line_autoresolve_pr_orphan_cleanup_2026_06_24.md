---
title:
  Cure-B `auto-resolve/version-line-<sha>` PRs orphan and accumulate as DIRTY cruft — `auto_resolve_version_promote.sh`
  closes the `staging→main` PR it supersedes but never closes the auto-resolve PRs IT creates, so each re-run leaves the
  prior one open; main advances past them → they go DIRTY and sit in the triage queue until closed by hand.
created: 2026-06-24
status: active
priority: P2
source:
  - 2026-06-24 first-hand: manually closed 6 such orphan PRs across 5 repos (verified superseded via two-dot tip diff vs
    main + LDR SSOT, NOT commit-count): mtds #370/#372/#374, deployment-ui #318, features-service #663
  - scripts/cicd/auto_resolve_version_promote.sh (creates BR=auto-resolve/version-line-<sha> L47; closes ONLY the
    triggering staging→main STALE_PR at L55; no cleanup of prior auto-resolve PRs)
  - .github/workflows/staging-to-main.yml (invokes auto_resolve at the dirty branch; re-runs every */15 + on dispatch)
  - plans/active/issues/staging_main_version_line_dual_lineage_2026_06_22.md (Cure B design — closes the staging→main PR
    only; does not address its own auto-resolve PRs orphaning)
locked_by: live-defi-rollout
---

> **Scope guard (read first).** The version-line _conflict_ mechanism, the multi-day _jam_ (drain-net outage, FIXED PR
> #490), and the Mode-A/B promoter-skip are ALREADY documented in three active docs: `dual_lineage`, `divergence`, and
> `staging_to_main_promotion_starvation_2026_06_19.md`. **This doc is NOT a re-file of those.** It is the one _residual_
> gap none of them address: the lifecycle of the `auto-resolve/version-line-<sha>` PRs that **Cure B itself creates**.
> Do not duplicate the broad analysis here.

## What I found (first-hand, 2026-06-24)

`auto_resolve_version_promote.sh` (Cure B) fires whenever a `staging→main` promote is version-line-DIRTY. Each run:

1. creates a fresh branch `auto-resolve/version-line-<short-sha>` (L47),
2. opens a "chore(release): promote staging->main (version-line auto-resolved)" PR to `main` with `--auto --rebase`,
3. **closes the `staging→main` STALE_PR** it superseded (L55).

It does **NOT** close any _prior_ `auto-resolve/version-line-*` PR for that repo. So if its own PR does not merge
first-try — its v2 fails (commonly a stale-dep `ImportError`, e.g. mtds branches pinned a UAC that predated
`BARCHART_VIX_FIRST_DATE`), or `main` advances before it merges — and Cure B fires again on the next `*/15` tick, it
opens `auto-resolve/version-line-<sha2>` and leaves `<sha1>` open. They stack:

- **market-tick-data-service** accumulated **3 simultaneously** (#370 @08:38, #372 @09:57, #374 @11:08 UTC — one per
  run).
- Once `main` promotes past them (e.g. mtds main reached 0.68.0 while the branches carried 0.66.0), the two-dot tip diff
  flips: the branch now **lacks** content `main` has → the PR goes **DIRTY** and, if merged, would _delete live content
  from main_ (deployment-ui #318 would have dropped ~297 lines incl. the current `Deployments.tsx`; features #663 would
  have dropped `mvp_universe_filter.py` 223 lines).

**Net:** they are inert orphans that never merge and never self-close. I closed **6** by hand today (REST
`PATCH state=closed` + a superseded comment), all created 08:38–12:12 UTC — i.e. **post the 2026-06-22 Cure-B/jam
mitigations**, so the existing fixes do not cover this.

## Why it matters

- **Triage-queue noise that masquerades as systemic QG failure.** Each orphan shows OPEN + DIRTY + (often) a red v2,
  indistinguishable at a glance from a real promotion blocker — the operator repeatedly flagged these as "stuck PRs."
- **Merge-hazard if mis-triaged.** A naive "unblock the stuck PR" (rebase + admin-merge) on a stale orphan would
  _regress main_ (delete live content). The only correct disposition is close-as-superseded, which today is manual.
- **Recurs structurally**, not transiently: any repo whose first auto-resolve PR doesn't merge before the next `*/15`
  tick generates a fresh orphan; the rate scales with v2-flakiness + promote cadence.

## Recommended decision (for the CICD-pipeline owner)

Make Cure B clean up after itself — pick the least-invasive that fits the promoter design:

1. **Supersede-on-create (preferred):** in `auto_resolve_version_promote.sh`, before opening the new PR, enumerate the
   repo's existing open `head:auto-resolve/version-line-*` PRs and `gh pr close --delete-branch` them as superseded
   (they are by construction older bumps of the same line). O(1) extra `gh` calls, keeps ≤1 auto-resolve PR per repo.
2. **Janitor sweep:** a small periodic step (fold into `ci_failure_watcher.py` or `promotion_lag_monitor.py`) that
   closes any open `auto-resolve/version-line-*` PR whose **two-dot tip diff vs `origin/main`** has zero genuine (non
   version/lock/manifest) files OR is net-negative (branch behind main) — the exact superseded test I used by hand.
   Fail-safe: only ever _closes_, never merges; skip `breaking_pending` repos.

Either is bounded + reversible (PRs can be reopened). Option 1 prevents accumulation at the source; option 2 also reaps
historical orphans. Verify by re-running the census `gh pr list … head:auto-resolve/version-line` fleet-wide → expect 0.

## Secondary observation (context, not the ask)

A separate, **self-healing** instance also showed up today and needs no fix: deployment-service **#256**
(`staging→main`) failed v2 on a real `check-import-patterns` violation in `scripts/vm/vm_zombie_watchdog.py` (a
`# noqa: qg-deep-import` placed on the _continuation_ line, which the checker does not honor — per the CLAUDE.md rule it
must sit on the `from` line). LDR had **already fixed** the placement (commit `ef8b4cd`, "noqa placement …
gate-unblock"); the PR was just testing **stale staging** until the LDR→staging drain caught up — it then went green and
**merged on its own**. Logged only so a future triager doesn't mistake the promotion-lag window for the orphan-PR class
above.
