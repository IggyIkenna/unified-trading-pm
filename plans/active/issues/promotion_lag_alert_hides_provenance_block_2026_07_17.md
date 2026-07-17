---
doc_type: issue
title:
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
asset_group: [cross-cutting]
stage: [infra]
repos: [unified-trading-pm, market-tick-data-service, deployment-ui]
scope: [engineer]
tags: [cicd, promotion, provenance-gate, quickmerge, alerting, branch-health]
related:
  [
    "codex/08-workflows/ci-cd-flow.md",
    "codex/04-architecture/ci-alerting.md",
    "plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md",
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
   dig every time. Dedup by state-transition per `codex/04-architecture/ci-alerting.md` (fire on change / RESOLVED /
   re-remind), never every tick.
2. **[OPERATOR] P2 — clear the two current blocks at source** (owner of the bypassed code, NOT this session):
   - `market-tick-data-service@d302f07a` — re-ship via `quickmerge --agent --files '<paths>'`, or revert on LDR.
   - `deployment-ui` — same; identify its offender the same way (`git log origin/main..origin/live-defi-rollout` + check
     each commit for a `Quickmerge:` trailer). **Do NOT hand-arm auto-merge on either.**
3. **[DOCS] P3** — the `_backmerge` merge commits (`Merge remote-tracking branch 'origin/main' into _backmerge`) also
   lack trailers and appear in the same scan; confirm they are carve-out-exempt in `check_strict_quickmerge.py` so
   future triage does not chase them as offenders.

## Provenance

Found while shipping `bucket_estate_consolidation_to_sub100_2026_07_13`'s asset-group parity sweep (operator shared the
branch-health alert mid-session, "still 2 left"). Diagnosed read-only: `gh api compare` for content, `gh pr list` for
merge state, `gh api issues/<n>/comments` for the marker, `gh run view --log` for the bot's own reasoning, and a trailer
scan of `origin/main..origin/live-defi-rollout`. Neither repo was touched.
