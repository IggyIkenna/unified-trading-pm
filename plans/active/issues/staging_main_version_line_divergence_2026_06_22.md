---
title:
  staging→main promote PRs recur as version-line (pyproject) conflicts — dual-path version divergence; the LDR→main
  fallback drains them but they regenerate every cycle (structural cure = single-lineage version stamping)
created: 2026-06-22
source:
  - 2026-06-22 triage-queue investigation (deployment-ui /repos "Stuck — triage queue")
  - instruments-service git history (merge-base 9c0d29b / main tip "Merge PR #511 from live-defi-rollout")
  - .github/workflows/staging-conflict-ldr-main-fallback.yml (the live Class-D mitigation)
  - .github/workflows/conflict-resolution-agent.yml (dup-env outage, fixed 2026-06-22)
  - .github/workflows/semver-agent.yml.tmpl (bump fires on push:[staging], not LDR)
locked_by: live-defi-rollout
parent_epic: infrastructure_master
estimate_class: design
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.2
priority: P1
status: active
resolution:
  REOPENED 2026-06-22 (slot-3) — operator OVERRODE the false-positive/no-action close ("fix this properly"). The
  mechanism below is now VERIFIED first-hand (not relayed) and the acute multi-day JAM is confirmed RESOLVED, but the
  structural cure to stop the conflicts RE-FORMING is pending an operator approach-decision (B vs A vs C). The prior
  RESOLVED banner is retained but SUPERSEDED.
---

> ## ⚠️ REOPENED 2026-06-22 (slot-3) — operator override; VERIFIED root cause + final cure (supersedes the FALSE-POSITIVE banner below)
>
> **Verified first-hand (not relayed).** `git log -p pyproject.toml` on `instruments-service` and `agent-orchestrator`
> `main` shows the `version =` line written by **two interleaved bot lineages**: `semver-agent[bot]` sequential
> `chore(release): bump to X` (the gated `--rebase` promote) AND `uts-ci-poller[bot]` `feat: LDR → staging (Tier C
> auto-drain)` commits landing on `main` (the LDR→main drain). ao bumped **14× in 20 h** (one commit per bump) → the hot
> line churns fast and is written by both lineages.
>
> **Mechanism (proven, not inferred):** `staging→main` promotes via `--rebase`, replaying staging's individual bump
> commits onto `main`. When `main`'s version line was last written by the DRAIN lineage (not the bump sequence), the
> rebase conflicts on that one line. The Class-D `LDR→main` fallback that drains the conflict writes the line via the
> drain lineage AGAIN → **seeds the next conflict** → self-perpetuating treadmill.
>
> **Why it became a multi-day JAM (the amplifier the prior banner missed):** the escalation worker
> `conflict-resolution-agent` was a **SILENT OUTAGE** — a duplicate `env:` block (Max-plan-worker cutover regression)
> made it invalid YAML so every dispatch failed with **no failure alert**. With the drain net dead, the transient
> version-line conflicts piled up fleet-wide for days. Fixed 2026-06-22 (PR #490) + the weekend Mode-A/B
> version-recording fixes (`staging_to_main_promotion_starvation_2026_06_19.md`).
>
> **Current health (verified 2026-06-22):** 23/25 repos have `version` IDENTICAL across main/staging/LDR;
> `staging-to-main` + Class-D fallback + `conflict-resolution-agent` all GREEN; only `agent-orchestrator` shows a benign
> 1-bump lag. The pipeline self-heals again — the acute jam is RESOLVED.
>
> **FINAL CURE — make conflicts NEVER form (not just drain). Remove the dual-lineage on the version line. Operator picks
> the approach (fleet-wide release-flow → blast radius):**
>
> - **(B) RECOMMENDED — version-line-neutral drains.** The LDR→main drain lineage must NOT write `version =`; `main`'s
>   version advances ONLY via the gated `staging→main` promote. Removes the second writer → no dual-write → no rebase
>   conflict. Targeted (the drain/backmerge workflows + a version-line keep-ours policy). Does **not** touch `--rebase`
>   (no BEHIND regression), no routine force-sync, no `strict` change — avoids every pitfall the prior audit flagged.
> - **(A) dynamic/tag version.** Stop committing the bump; derive version from a git tag (`dynamic`). Zero version-bump
>   commits → zero conflict surface. Cleanest long-term, highest blast radius (every repo's build + semver-agent +
>   manifest reader).
> - **(C) accept the now-healthy reactive equilibrium** (the prior stance) — drains self-heal it; the flicker is
>   cosmetic. Operator already leaned here; now overridden.
>
> **Defense-in-depth (independent of the cure, low-risk, ship-able now):** neither `conflict-resolution-agent` nor the
> Class-D fallback alerts on its OWN failure — `promotion-lag-monitor` only catches the lagging *symptom* (days late).
> Add a drain-net workflow-health alert so a silent outage can never again become a multi-day jam.
>
> ---
>
> ## ✅ RESOLVED 2026-06-22 — FALSE POSITIVE (by-design trade-off, NO action) — **SUPERSEDED by the REOPENED banner above**
>
> Full audit concluded this is **not a defect** and **no change should be made**. The recurring `version =` conflict is
> the deliberate, accepted cost of the topology — every proposed cure was audited and rejected:
>
> - **Option-2 (promoter auto-resolves version line):** REDUNDANT — the live `staging-conflict-ldr-main-fallback`
>   already drains this conflict class via clean `LDR→main` routing. A second resolver = competing parallel path.
> - **4a (`staging→main` `--rebase`→`--merge`):** UNSAFE — reverts the deliberate fix `0a76d0103` ("promote via --rebase
>   not --merge so staging never diverges from LDR"). `--merge` creates merge nodes → target diverges from LDR → the
>   next promote PR goes **BEHIND** → blocked by "require branches up to date" (`strict`). Audit found **6 repos still
>   `strict=True`** (market-data-processing, trading-agent, client-reporting-api, deployment-api, ibkr-gateway-infra,
>   system-integration-tests) → `--merge` would reintroduce the deadlock there. (All 24 allow merge commits / none
>   require linear history — feasibility was fine; the BEHIND regression is the blocker.)
> - **4b (routine force-sync staging/main ← LDR):** REJECTED — force-sync is operator-gated CI/CD-repair only, never a
>   routine promotion model.
> - **strict-standardization (turn `strict` off fleet-wide → then `--merge`):** REJECTED by operator — at 200-300
>   commits/day across the fleet, dropping the up-to-date guarantee / changing promotion would gut velocity. Not worth
>   it.
>
> **Net:** the `--rebase` topology + the Class-D `LDR→main` fallback + the (now-fixed) conflict-resolution-agent is the
> correct, deliberately-chosen equilibrium. The version-line conflicts are auto-drained reactively; that is acceptable.
> The "What I found" / mechanism analysis below is RETAINED only so this is never re-investigated — it is NOT a backlog
> item. Everything under "## Recommended decision" is SUPERSEDED by this banner.

## What I found

`staging→main` promote PRs across the fleet recur as CONFLICTING on a single deterministic thing: `pyproject.toml`'s
`version =` line. On 2026-06-22 the triage queue showed 6 such PRs; after they drained, **7 new ones appeared within the
hour** (UAC#412, instruments#514, fund-admin#219, greeks#238, unified-trading-api#429, e2e-testing#366, SIT#257). It is
a **treadmill** — drained reactively, regenerated every promote cycle.

### Root cause — dual-path version-line divergence (verified on instruments-service)

The version is **not** bumped on LDR. `semver-agent` fires on `push:[staging]` (the staging gate: "feature → staging →
bump → SIT → main") and commits `chore(release): bump version to X` **on staging**; the bump then backmerges down to LDR
(so all three branches end up carrying the bump commit). So versions are not missing — every branch gets them.

The conflict comes from `main` having **two inbound lineages** that both touch the `version =` line:

1. the gated `staging→main` release promote (carries the bumped version), and
2. the `LDR→main` drift/fallback merge (carries LDR content).

Traced on instruments-service: merge-base(staging,main) = `9c0d29b` (`version 0.25.0`); main's tip =
`6c91953 "Merge pull request #511 from live-defi-rollout"`. LDR carried the staging-bumped `0.27.0`, but that LDR→main
merge **kept main at `0.25.0`** (main must not jump to an un-released version outside the gated promote) — i.e. it
**re-resolved the `version =` line on main's side**. That re-resolution diverges main's version-line history from
staging's, so the next `staging→main` promote sees "both sides changed the version region" → textual conflict that never
self-heals. It is NOT a missing/misplaced bump; it is a hot line edited by two lineages into `main`.

## Why it matters

- Recurring triage churn: every promote cycle regenerates a batch of version-line conflict PRs across ~the whole fleet.
- Latency: the live mitigation runs hourly with a 30-min staleness floor, so a conflicted promote can sit "conflict
  wall" for up to ~90 min before draining — that is the "Stuck — triage queue" the operator sees.
- It masks real conflicts: a genuine (non-version) staging→main conflict is harder to spot in the noise.

## Live mitigations (already shipped — do NOT duplicate)

1. **`staging-conflict-ldr-main-fallback.yml` (Class D, hourly `47 * * * *`, STALE_MIN=30)** — the architecturally
   correct workaround: instead of resolving the version line, it **routes the promotion through an `LDR→main` PR**.
   Because LDR is the SSOT and carries BOTH back-merges (LDR ⊇ main AND LDR ⊇ staging), `LDR→main` is a CLEAN merge that
   lands the same+newer content; it verifies `main...LDR behind_by==0`, arms v2-gated auto-merge (`--merge`, non-admin),
   and closes the dammed `staging→main` PR as superseded. SAFETY: skips `breaking_pending` repos; never
   force/admin-merge.
2. **`conflict-resolution-agent.yml`** — the worker-escalation path for non-trivial conflicts. **Was a silent outage**
   2026-06-22: a duplicate `env:` block in the dispatch step (Max-plan-worker cutover regression) made the workflow
   invalid YAML → every `repository_dispatch` failed to start → escalated conflicts went nowhere. **FIXED**
   (`fix(cicd): conflict-resolution-agent — merge duplicate env: blocks`, PR #490 → main); dispatch verified working.

## A dedicated version-line auto-resolver was considered and REJECTED as redundant

A "promoter auto-resolves the version-line-only conflict (take higher semver + `uv lock`)" fix was proposed + approved
in principle, but on reading the existing workflows it duplicates the Class-D fallback (which already drains exactly
this conflict class, more cleanly, via LDR→main). Adding a second resolver would be a competing parallel path (violates
delete-deprecated / no-parallel-paths). **Decision: do not build it.** The fallback + the now-fixed agent cover the
reactive drain.

## Recommended decision (SUPERSEDED — see ✅ RESOLVED banner at top; retained for history only)

1. **Structural cure (this issue) — single-lineage version stamping.** Make the `version =` line have ONE history so it
   cannot diverge:
   - Bump on a single lineage consistent with LDR-is-SSOT (stamp once; staging + main are byte-identical projections),
     OR
   - keep the staging bump but make the `LDR→main` path **version-line-neutral** (never re-resolve `version =` on main —
     main only ever takes the version via the gated `staging→main`/`LDR→main` promote, never via a drift merge). Either
     removes the dual-lineage edit of the version line → no recurring conflict → the Class-D fallback becomes rarely
     needed. Touches `semver-agent` bump location + the backmerge + promote topology → needs a careful pre-audited plan
     (Citadel-grade: grep every consumer of the version-bump/backmerge flow before changing it).

2. **Cheap latency win (optional, decide separately):** tighten `staging-conflict-ldr-main-fallback` from hourly to
   `*/20`–`*/30` so the conflict-wall dwell time drops from ~90 min toward ~30 min. Tradeoff: more Actions runs; the
   comment deliberately set it hourly as "low-urgency". Operator call — does NOT fix recurrence, only latency.

## ⚠️ Paths to explore more (not yet verified)

- **Confirm the `LDR→main` drift merge is the ONLY second writer of `version =` on main** (vs e.g. a backmerge bot or a
  ci_status commit also touching it). Trace 2–3 more repos' main version-line history before designing the cure.
- **Whether bumping on LDR would prematurely leak un-released versions to main** via the LDR→main drift path — the cure
  must keep main's version advancing ONLY through the gated promote, even if the stamp lineage moves to LDR.
- **Interaction with the Mode-A/Mode-B findings** in `staging_to_main_promotion_starvation_2026_06_19.md` (the manifest
  version-bump desync + the squash-fallback semver-label loss) — all three touch the same version/promote machinery; the
  cure plan should reconcile them so fixes don't fight.
