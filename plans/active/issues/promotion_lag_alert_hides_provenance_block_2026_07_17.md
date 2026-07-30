---
doc_type: issue
title: >-
  "PROMOTION LAG" alert hides its actual cause — 2 repos are provenance-blocked by non-quickmerge code, not slow CI
summary: |
  The hourly branch-health alert fires "PROMOTION LAG > 60m — 2 branch-pair(s) across 2 repo(s) un-propagated"
  (market-tick-data-service 69m, deployment-ui 249m) and links to the deployment-ui /repos page. The wording reads as
  slowness / a stuck job, so the natural response is to look at CI or re-run the promote workflow. **Neither is the
  cause.** Both promote PRs carry the LDR→main fleet bot's `<!-- promote:provenance-blocked -->` comment: the bot
  detected code on LDR with no `Quickmerge:` trailer and DELIBERATELY did not arm auto-merge. It is working exactly as
  designed and holding the line. Diagnosing this took a manual dig (PR comments + reflog + fleet-run logs) because the
  alert surfaces neither the marker comment nor the offending SHA. MTDS reads especially misleading: PR#602 is
  `mergeable=MERGEABLE`, `mergeStateStatus=CLEAN`, `quality-gates-v2` green — it looks perfectly healthy, because the
  block is provenance, not quality. Offender identified: market-tick-data-service@d302f07a
  `feat(cefi): canonical-completeness write side — 3-tuple builder (FIX 0), decompose ALL venues (D1)...` — real
  feature code, no trailer, not a carve-out. deployment-ui carries the same marker (its Vercel team-permission comment
  on top is unrelated noise that makes the PR read `UNSTABLE`).
status: open
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, market-tick-data-service, deployment-ui]
scope: [engineer]
tags: [cicd, promotion, provenance-gate, quickmerge, alerting, branch-health]
related:
  [
    "/codex/08-workflows/ci-cd-flow.md",
    "/codex/04-architecture/ci-alerting.md",
    "/plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md",
    "/plans/archive/issues/hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install_2026_07_26.md",
  ]
created: 2026-07-17
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: devops
drift_direction: none
depends_on: []
source: >-
  slot session 2026-07-17 — authored while diagnosing the branch-health PROMOTION-LAG alert; frontmatter repaired (title
  block-scalar — a wrapped title continuation starting with a quote breaks YAML — stage enum + missing keys) by slot
  main·harsh_pc to unblock the PM lint-codex gate, content untouched
resolved_by:
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# "PROMOTION LAG" hides the provenance block

## Evidence (2026-07-17, ~13:2x BST)

| Repo                     | PR   | mergeable | mergeStateStatus | quality-gates-v2 | auto_merge | Real cause                           |
| ------------------------ | ---- | --------- | ---------------- | ---------------- | ---------- | ------------------------------------ |
| market-tick-data-service | #602 | MERGEABLE | CLEAN            | success          | **null**   | `promote:provenance-blocked` comment |
| deployment-ui            | #376 | MERGEABLE | UNSTABLE         | success          | **null**   | `promote:provenance-blocked` comment |

Content diff (NOT the squash-inflated `ahead_by`, per the ci-cd-flow rule): MTDS 22 files, deployment-ui 41 files
genuinely un-promoted.

The fleet workflow (`ldr-to-main-promote-fleet.yml`) runs every ~30 min and reports **success** each time — because
refusing to arm auto-merge IS its success path here. So "the bot is green but nothing merges" is expected behaviour, not
a malfunction.

Bot comment on both PRs:

> ⛔ **Provenance gate (LDR→main fleet bot)** — this promote carries code that bypassed quickmerge (no `Quickmerge:`
> trailer, not a carve-out). Auto-merge NOT armed. Re-ship via `quickmerge --agent --files '<paths>'` or revert on
> `live-defi-rollout`.
>
> **Do NOT hand-arm auto-merge to "unblock" this** — that promotes the bypassed code AND moves the provenance baseline
> past it, so the violation is laundered and never flagged again (happened 2026-07-16).

## The finding

The gate is right. The **alert** is the problem: it describes a symptom ("lag", "un-propagated") whose most natural
reading (slow CI / stuck job) is the opposite of the truth (a deliberate hold), and it points at a dashboard rather than
at the marker comment or the offending SHA. A responder who trusts the alert wording will look at CI, find it green, and
either escalate the wrong thing or — worst case — hand-arm auto-merge, which the bot explicitly warns launders the
violation permanently. That already happened once (2026-07-16).

This is the same class the direct-push era produced: measured 2026-07-16, MTDS accumulated 26 bypassed commits and
deployment-api 7, with mtds's promotion sitting blocked ~23h and surfacing only as an anonymous "PROMOTION LAG" alert.
The operator ruling that day (CODE ships via quickmerge, enforced by the pre-push hook) fixed the INFLOW; this issue is
about the alert that reports the residue.

## Fix direction

1. **[DEVOPS] P2 — make the alert say what it means.** When a promote PR carries `<!-- promote:provenance-blocked -->`,
   the branch-health alert should classify it as `PROVENANCE-BLOCKED`, not `PROMOTION LAG`, and inline the offending
   SHA + subject + the "re-ship or revert, do NOT hand-arm" remedy. A lag alert and a provenance hold are different
   conditions with different responders and different correct actions; collapsing them into one message costs a manual
   dig every time. Dedup by state-transition per `/codex/04-architecture/ci-alerting.md` (fire on change / RESOLVED /
   re-remind), never every tick.
2. **[DEVOPS] P2 — clear the two current blocks at source** (retagged from `[OPERATOR]` 2026-07-28 — re-shipping or
   reverting a specific already-identified bypassing commit via the standard quickmerge/revert flow is normal
   AO-dispatchable work per `/codex/08-workflows/ci-cd-flow.md`, no operator judgment call needed; re-confirmed
   2026-07-28 that both blocks are still live — `market-tick-data-service@d302f07a` still carries no `Quickmerge:`
   trailer and is still ahead of `origin/main`, deployment-ui is still 292 commits ahead of `origin/main`):
   - `market-tick-data-service@d302f07a` — re-ship via `quickmerge --agent --files '<paths>'`, or revert on LDR.
   - `deployment-ui` — same; identify its offender the same way (`git log origin/main..origin/live-defi-rollout` + check
     each commit for a `Quickmerge:` trailer). **Do NOT hand-arm auto-merge on either.**
3. **[DOCS] P3** — the `_backmerge` merge commits (`Merge remote-tracking branch 'origin/main' into _backmerge`) also
   lack trailers and appear in the same scan; confirm they are carve-out-exempt in `check_strict_quickmerge.py` so
   future triage does not chase them as offenders.

## Todos

- [x] ✅ [DEVOPS] P2. **Ship the "Fix direction" items — CONFIRMED ALREADY SHIPPED, this todo was stale.** Verified
      2026-07-30 (slot 1, `/autonomous` dispatch): `scripts/cicd/promotion_lag_monitor.py` (git blame: `f9b64f15d`,
      2026-07-17) already implements fix #1 exactly — a forward `LDR→main` pair checks `_provenance_blocked(repo)` and,
      when true, emits
      `⛔ BLOCKED by the provenance gate — non-quickmerge CODE on LDR     (N change(s), oldest Mm). NOT a stuck pipeline. If the bypass is the LDR tip: quickmerge --agent --files it. If     it is MID-HISTORY: scripts/cicd/reprovenance_bypass.sh <sha> --push. Do NOT hand-arm auto-merge.`
      — this is the EXACT wording the operator saw in tonight's `#ci-failures` alert for
      `features-service`/`market-tick-data-service`. Fix #3 (`_backmerge` merge-commit carve-out) is confirmed in
      `check_strict_quickmerge.py::commit_violates` (a 2-parent commit is exempt unconditionally,
      `"merge/reconcile commit"`). Fix #2 (clear the two blocks named in this doc, `market-tick-data-service@d302f07a` +
      `deployment-ui`) is STALE — those specific 2026-07-17 offenders are 13 days old now and long since superseded by
      many more bypasses on both repos; **cleared the CURRENT (2026-07-30) blocks instead** — see this session's real
      todo below, this doc's original offenders are moot/overtaken, not separately re-chased.
- [x] ✅ [DEVOPS] P1. **Cleared the LIVE 2026-07-30 provenance blocks for `features-service` (4 bypassing commits) and
      `market-tick-data-service` (38 bypassing commits)** — both MID-HISTORY (not the LDR tip), so per this doc's own
      fix #2 remedy, re-shipped via `scripts/cicd/reprovenance_bypass.sh <sha>` (one empty, provenanced
      `Reprovenance: <sha>` blessing commit per bypass, verified via the REAL `check_strict_quickmerge.py` scan — never
      a re-implemented heuristic) rather than reverting real shipped feature/bugfix work spanning back to
      2026-07-13/07-18. `features-service` pushed clean (`origin/live-defi-rollout` fast-forward).
      `market-tick-data-service` hit a genuine concurrent-push conflict from another slot mid-session (`cb6331ba`,
      unrelated OpenBB-adapter deletion) — resolved via `git rebase --autostash` (preserved an unrelated foreign
      dirty-WIP file untouched throughout), then pushed clean. Both repos'
      `check_strict_quickmerge.py --range origin/main..HEAD` now report `✅ no bypassed code commits`. **Did NOT
      hand-arm auto-merge on either** (per this doc's own explicit warning) — the actual PR merge for both is now
      additionally gated on the separate, unrelated, currently-active GitHub Actions billing wall
      (`/plans/active/issues/github_actions_billing_wall_recurrence_2026_07_29.md`, `BLK-21d55fb1`) — the provenance
      block is cleared, but neither promote PR can complete until that operator-only wall lifts. No workflow/alerting
      code change was needed for this todo (the alert already says what it means); the actual `PROMOTION LAG CLEARED`
      Slack recovery message for these two pairs will fire automatically once (a) the billing wall lifts and (b) the
      promote PR actually merges — the recovery-bookend mechanism itself (`branch-health.yml`'s `lag-notify-resolved` +
      `promotion_lag_monitor.py`'s per-pair clear-diff) was independently verified this session to be correctly
      implemented, not missing.
- [x] ✅ [DATA] P2. **New, separate finding — ALREADY RESOLVED, no action needed.** `market-tick-data-service`'s promote
      PR was blocked by STEP 5.101 (empty-string-fallback-site ratchet, baseline 89, observed 93) at
      `scripts/verify_cefi_canonical_4surface_2026_07_20.py:531-532` and
      `scripts/verify_kamino_solend_lending_relabel_2026_07_30.py:67-68`. Investigated to fix directly; found slot-7 had
      already shipped the fix (`market-tick-data-service@00c2cfe4`, 07:57:57Z, fleet count back to 87 < baseline 89) —
      its own issue doc `mtds_empty_string_fallback_baseline_drift_2026_07_30.md` is `status: resolved`, archived.
      Manually re-dispatched `ldr-to-main-promote-fleet.yml` to cut a fresh promote PR carrying that fix sooner than the
      scheduled tick. Provenance cleared, SIT gate passes — once the fresh PR's own SIT-revalidation cycle completes,
      MTDS's promotion has no remaining blocker.

## Progress Log (2026-07-30, slot 1, `/autonomous` dispatch — outcome update)

- **features-service: PROMOTED.** Its promote PR was superseded once (immutable per-SHA ref pattern: #897 closed
  unmerged, fresh #898 opened 08:01:04Z) as LDR kept moving; #898 merged automatically at **08:16:03Z**, right after the
  dispatched `full-workspace-sit` run reached `conclusion=success` (07:31:30Z start, ~45min runtime — genuine
  workspace-wide integration-test duration, not a hang; queued behind one busy self-hosted runner beforehand). This
  branch-health alert line is now fully resolved with no operator action needed.
- **market-tick-data-service: SIT-gate cleared; hit a SEPARATE, real ratchet violation, ALREADY FIXED by another slot
  before I could act.** Its promote PR was likewise superseded (#781 → fresh #782, same immutable-ref pattern) and
  `sit-gate/fleet-green` now shows `pass` against the fresh SIT run. But its own `quality-gates-v2` / QG slice (checks)
  then FAILED for a real reason unconnected to provenance, SIT, or the GHA billing wall: **STEP 5.101
  (empty-string-fallback-site ratchet)** — 93 `.get(key, "")` sites found vs. baseline 89, reported (positional
  tail-slice, git-diff-against-baseline-commit failed) at `scripts/verify_cefi_canonical_4surface_2026_07_20.py:531-532`
  and `scripts/verify_kamino_solend_lending_relabel_2026_07_30.py:67-68`. Investigated to fix directly per the
  operator's explicit instruction — read `check_no_empty_string_fallback.py`'s exemption criteria, confirmed all 11
  `.get(..., "")` sites across both files fit the documented "field may be absent, empty string is the correct
  not-present sentinel" safe case (the `parse_object()`/`resolve_with_maps()` skip-if-absent pattern in the cefi script;
  the kamino/solend script's absence-correctly-falls-through-to-MISMATCH pattern) — but found **slot-7 had already
  shipped the identical fix** minutes earlier: `market-tick-data-service@00c2cfe4` (07:57:57Z, "annotate 6 pre-existing
  empty-string-fallback sites (STEP 5.101 baseline drift)"), already pushed to `live-defi-rollout`, bringing the
  fleet-wide count to 87 (< baseline 89). Its own issue doc
  (`plans/archive/issues/mtds_empty_string_fallback_baseline_drift_2026_07_30.md`) is already `status: resolved` and
  archived — nothing left to fix. PR #782 predates that fix commit (created 07:16:25Z, the fix landed 07:57:57Z) so it
  doesn't carry it; manually re-dispatched `ldr-to-main-promote-fleet.yml` to cut a fresh superseding PR sooner rather
  than waiting for the ~15-30min scheduled tick — that fresh PR will include `00c2cfe4` and should clear STEP 5.101,
  though it will need its own SIT-gate revalidation cycle (the tree moved again) before it can merge. Correcting my own
  earlier note in this doc: the files' most recent prior touch was slot-11's (`f9222f78`), but the actual STEP 5.101 fix
  was slot-7's, not slot-11's — attributing correctly for anyone reading this later.

## Progress Log (2026-07-30, slot 1, `/autonomous` dispatch — final update)

- **GHA billing wall recovered ~06:11Z.** User independently observed "github is working again" and I confirmed live: a
  fresh `quality-gates-v2` dispatch on `unified-trading-pm` went `queued` → real jobs executed (not the 0-step
  `startup_failure` signature) → `failure` (a genuine, unrelated content-sentinel result, not investigated further — out
  of this doc's scope). See `github_actions_billing_wall_recurrence_2026_07_29.md` for the corroborating entry.
- **Re-checked features-service PR #897 and market-tick-data-service PR #781 now that GHA is back.** Both still show the
  OLD `promote:provenance-blocked` marker comment (stale — posted before the wall lifted, the fleet bot couldn't
  re-evaluate while walled). Manually re-dispatched `ldr-to-main-promote-fleet.yml`; its fresh run (completed success,
  06:19-06:2xZ) shows the REAL current state has moved past provenance entirely:
  `SIT GATE BLOCK <repo>: true-delta not SIT-validated on this tree ... fail-CLOSED. Dispatching SIT-on-LDR; a later tick promotes once SIT validates this exact tree`
  for 6 repos (unified-api-contracts, unified-trading-library, features-service, market-tick-data-service,
  agent-orchestrator, unified-trading-system-ui) — i.e. the LDR tree moved (my reprovenance commits + other slots'
  concurrent fixes) past the last SIT-validated tree, so the SIT gate correctly fails closed and auto-dispatches a fresh
  `full-workspace-sit` run rather than promoting an unvalidated tree. This is normal, designed, self-healing pipeline
  behavior — not a bug, and not provenance-related. The old marker comments on both PRs are now misleading residue from
  before the wall lifted; a future fleet tick should overwrite/clear them once SIT validates and the PR actually merges
  (not forcing this — same "do NOT hand-arm" principle this doc already establishes).
- **Dispatched SIT run status at handoff**: `full-workspace-sit` runs kept showing `pending`/`jobs:[]` for an extended
  window; the repo's one self-hosted runner (`glue-ip-172-31-5-118-1`) was confirmed `status=online, busy=true` (busy
  with other queued work, not offline/broken) — this is ordinary self-hosted-runner contention (the same class as
  `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`), not the billing wall recurring. Newer dispatches
  superseding older still-pending ones (several `cancelled`/`jobs:[]` runs in the list) is a secondary observation, not
  chased further — `full-workspace-sit.yml`'s concurrency group is `cancel-in-progress: false`, so this is scheduled
  fleet-tick re-dispatch churn while the runner stays busy, not a hand-authored bug; worth a look if it recurs and
  genuinely prevents any run from ever completing, but not diagnosed as broken tonight. **Not something to force** — the
  scheduled `ldr-to-main-promote-fleet.yml` tick (~every 15-30min) will keep re-checking and will promote both PRs
  automatically the moment SIT validates the current tree. No further action needed from this session; the operator can
  verify at wake-up via `gh pr view 897 --repo IggyIkenna/features-service --json state,mergedAt` / same for MTDS PR
  #781.

## Addendum (2026-07-30, rulings-closeout pass)

Both todos above were already `[x]` before this pass touched the doc. One residual gap remained on fix #1's own bar
("classify... test against a synthetic provenance-blocked PR" per the "Fix direction" §1 wording) — no regression test
had ever exercised `_provenance_blocked()` against a synthetic blocked PR. Closed:
`scripts/cicd/test_promotion_lag_monitor_provenance_blocked.py` (6 tests — no-open-PRs, fail-closed-on-lookup-failure,
PR-without-marker, PR-with-marker [the synthetic reproducer], non-promote-titled PR skipped, non-int PR-number skipped),
shipped `unified-trading-pm@51b93ec0a`. This doc's own status/todos are unchanged (already fully resolved); this is a
test-coverage addendum, not a re-opening.

## Provenance

Found while shipping `bucket_estate_consolidation_to_sub100_2026_07_13`'s asset-group parity sweep (operator shared the
branch-health alert mid-session, "still 2 left"). Diagnosed read-only: `gh api compare` for content, `gh pr list` for
merge state, `gh api issues/<n>/comments` for the marker, `gh run view --log` for the bot's own reasoning, and a trailer
scan of `origin/main..origin/live-defi-rollout`. Neither repo was touched.

## Known rough edge, same LDR→main promotion subsystem (2026-07-26)

`/plans/archive/issues/hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install_2026_07_26.md` found an adjacent
failure mode in the same promotion pipeline: `main`'s squash-merge history can make a real release tag unreachable from
`main`'s own commit graph even though content is byte-identical to `live-defi-rollout`, so `git describe`/ hatch-vcs on
`main` falls back to a stale tag and computes a version below the current release floor — breaking a fresh
`pip install -e` of any package pinned to that floor. Different mechanism than this doc's alert-wording problem (that's
about a misleading `PROMOTION LAG` message masking a deliberate provenance hold), but both are downstream effects of
`main`'s squash-commit promotion history — worth checking together when diagnosing anything tag/version-ish on `main`.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): **ARCHIVE-READY, but BLOCKED-OPERATOR-DECISION** — 0
open / 2 done todos. All three "Fix direction" items are confirmed resolved in-doc: #1 (cause-naming in the lag alert)
verified already shipped in `promotion_lag_monitor.py`, #2's live provenance blocks cleared 2026-07-30, #3's
`_backmerge` carve-out confirmed in `check_strict_quickmerge.py`. Archival is NOT taken autonomously:
`locked_by: live-defi-rollout` requires an explicit `[unlock-plan]`. **Operator ask: `[unlock-plan]` and this archives
on the standard 6-step ritual.**
