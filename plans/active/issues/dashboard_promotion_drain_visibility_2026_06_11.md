---
title: "CI dashboard shows the breaking-cascade but NOT the routine LDR→staging/main promotion drain — operator can't see 'when did we last promote + did it pass'"
created: 2026-06-11
assignee: harsh
source:
  - operator observation 2026-06-11 (deployment-ui Repos CI: "Last SIT / cascade run — success 22h ago" — is that 'we haven't promoted in a day' or only the major-version cascade? we'd want to see when LDR→staging via auto-merge + QG branch protection last ran + its result)
  - slot-3 verification 2026-06-11 (cascade-qg-ordering vs ldr-to-staging-promote are distinct workflows)
locked_by: live-defi-rollout
priority: P2
status: active
---

# CI dashboard: promotion-drain visibility gap

## What I found

The Repos CI dashboard's **"Last SIT / cascade run"** panel sources **only** the breaking cascade
(`cascade-qg-ordering.yml`, PM-central), which **fires only on a real breaking / major-version public-surface change**
(`detect_breaking_change.py` verdict). So "cascade success 22h ago" means **no breaking change has occurred in 22h** —
it is **NOT** an indicator of routine promotion activity. An operator reasonably reads it as "we haven't promoted
anything in a day", which is wrong.

The **routine** promotion path is a **different, unsurfaced mechanism** (verified 2026-06-11):

- **`ldr-to-staging-promote`** (PM-central workflow, every **15 min**, fleet-wide) opens/reuses an auto-merging
  **LDR→staging** PR per repo; that PR's **`quality-gates-v2`** (head=LDR, base=staging) is the server gate. This is
  "are we pulling LDR→staging via auto-merge + QG branch protection".
- **`ldr-to-main-promote`** (PM-central, every 15 min) — the staging→main / standing-PR drain.
- These are **distinct** from `cascade-qg-ordering` (the panel's current source) and from SIT (which fires only on
  `breaking_pending` repos).

Today the dashboard surfaces none of: last LDR→staging promote run + result, last LDR→main promote run + result, or the
per-repo standing-promotion-PR + its v2 conclusion. The `branch_ci` chip (shipped deployment-api@e1878d2 +
deployment-ui@6632154) shows per-branch v2 _state_ but not the _promotion-drain run_ (when it last ran / passed / is
blocked).

## Why it matters

- **Composes with the alert-parity principle** (`monitoring_control_plane_master_2026_06_10.md`): anything we rely on
  (the promotion pipeline is flowing) must be a continuously observable state on the dashboard, not inferred from a
  panel that means something else.
- A stalled `ldr-to-staging-promote` (the bug #11 class — non-breaking content not draining staging→main) is **invisible
  today**; the operator only sees the unrelated cascade panel reading "success", masking a stuck routine drain.
- The operator explicitly asked for this signal: "when [are] we pulling repos from LDR to staging via auto-merge QG
  branch-protection workflow, when that was last run and the result".

## Recommended decision

Add a **"Promotion drain"** surface to the Repos CI dashboard (deployment-ui) backed by deployment-api, **distinct
from** the breaking-cascade panel and clearly labelled so the two are never conflated:

- [x] ✅ [CODE] P2. DONE-LOCAL 2026-06-12 (deployment-api@0232b5a, on LDR — billing-blocked from promotion). The
      aggregator exposes `promotion_drain` = last `ldr-to-staging-promote` + `ldr-to-main-promote` outcome
      (status/conclusion/age/url) via the Actions runs API. **Scoping note**: these are PM-CENTRAL workflows (not
      per-repo), so the drain runs are 2 GLOBAL queries (budget-friendly), NOT per-repo. The open standing per-repo
      LDR→staging / LDR→main PRs are already in `open_prs`; surfacing their per-PR v2 conclusion explicitly is moved to
      the P3 follow-up below. Repo: deployment-api (`repo_ci.py` reusing `latest_workflow_run_with_jobs`).
- [x] ✅ [CODE] [UI] P2. DONE-LOCAL 2026-06-12 (deployment-ui@367b5b7, on LDR — billing-blocked) | pw:L2 ✓ 200/200 |
      regression: tests/smoke/repos-tab.spec.ts. "Promotion drain" panel on `/repos` shows "LDR → staging: <result>
      <age>" + "LDR → main: <result> <age>" with a deep-link to the PM promote-workflow run. The existing panel is
      relabelled **"Breaking cascade / SIT"** so it's unambiguous it only fires on breaking changes. Repo: deployment-ui
      (`pages/RepoCi.tsx` `PromotionDrainPanel` + `lib/mock-api.ts`).
- [x] ✅ [CODE][UI] P3. **Stall surfacing + per-repo standing-PR v2** — flag when a repo has LDR content ahead of
      staging/main (real file delta, not squash skew) AND the last promote-drain run is stale/failing — i.e. the drain
      is stuck (bug #11 class), plus surface each standing LDR→staging/main PR's `quality-gates-v2` conclusion
      explicitly. Repo: deployment-api + deployment-ui. **Tracked in `monitoring_control_plane_master_2026_06_10.md`
      (promotion-drain follow-up).** — deployment-ui@788ad40 (`drain_stalled` backend = content-ahead AND blocking
      standing PR; row chip `drain-stalled-<repo>` + `PromotionDrainPanel` count/`drain-stalled-summary`) +
      deployment-ui@41c1c11 (explicit per-promotion-PR `quality-gates-v2` chip `pr-v2-<n>` in the repo drill-down). |
      pw:L2 ✓ (206 smoke passed) | regression: tests/smoke/repos-tab.spec.ts (`drain-stalled repo is flagged…` +
      `Each PR card carries an EXPLICIT     quality-gates-v2 state chip`). Backend `repo_ci.py` `drain_stalled` keys the
      stall on the repo's own blocking standing PR (the bug-#11 stuck-drain signal); a finer "drain-RUN stale/failing"
      axis can refine it later if needed.
- [x] ✅ [CODE][UI] P2. **Blocking required-check + reason on stuck PRs** (operator escalation 2026-06-15: two
      LDR→staging drain PRs sat stuck for days on a failing AWS-CodeBuild required check, but the Stuck-triage queue
      showed only a bare "Draining" chip with no reason — the operator had to escalate to find out it was the CodeBuild
      PR-approval gate). The Stuck panel now renders the actual non-success required check(s) + GitHub's reason string
      per PR (e.g. "✗ AWS CodeBuild ap-northeast-1 (deployment-service) — Pull request approval required for starting a
      build"). Root cause of the blind spot: `head_check_rollup` only reads Actions WORKFLOW runs, so a required check
      posted as a classic STATUS CONTEXT (AWS CodeBuild / any external CI) was invisible. — deployment-api@1a85dd71 (new
      `head_blocking_status_contexts` reads `/commits/{sha}/status` — Statuses:read, granted to the GH_PAT — +
      `blocking_checks: list[BlockingCheckDict]` on `RepoPrDict`, populated in `_repo_open_prs` + mock; route test
      `test_blocking_checks_surface_the_codebuild_reason`) + deployment-ui (RepoCi `StuckPanel` renders
      `stuck-pr-blocker-<repo>-<n>` lines; `RepoCiBlockingCheck` type + mock). | pw:L2 ✓ (207 smoke passed) |
      regression: tests/smoke/repos-tab.spec.ts (`a stuck PR shows the BLOCKING required check + reason`). Drive-by:
      fixed 2 pre-existing stale `GCSStorageClient` patch targets (factory → providers.gcp) broken by UTL's lazy-import
      refactor. Repo: deployment-api + deployment-ui.

**Parent epic**: `observability_master` (this is the monitoring control-plane surface). Wrapper into
`monitoring_control_plane_master_2026_06_10.md` smart-extras if picked up as a sub-plan, or execute directly from this
issue doc. Cold-start: worker reads `SUB_AGENT_MANDATORY_RULES.md`; the dashboard contract + click-through rules are in
`monitoring_control_plane_master_2026_06_10.md`.
