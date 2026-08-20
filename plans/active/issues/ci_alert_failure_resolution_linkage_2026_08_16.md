---
doc_type: issue
title: >-
  CI-failures Slack alerts carry no shared identity between a CRITICAL and its eventual
  resolution — fixed for QG-fail/QG-recovered, other alert pairs still unlinked
summary: >-
  Operator feedback (2026-08-16, during the `/autonomous` CI-debounce loop): reading the
  `#ci-failures` channel, it was not clear which "resolved/superseded" post corresponded to which
  earlier CRITICAL — two structurally different alert families share the same emoji/channel/source
  name but use different identity schemes. Promote-PR CRITICALs (`python-quality-gates-v2`) carry a
  PR number and the PM LDR→main drain-bot's "closed promote PR(s) #N as superseded... fresh promote
  PR is #N+1" INFO post does form an implicit chain — but never states "this resolves that
  CRITICAL," so a reader has to manually walk PR#N → PR#N+1 → ... themselves. LDR-push CRITICALs
  (`push to live-defi-rollout | sha ...`) carry no PR number at all, and their eventual resolution
  (`ldr-ci-monitor`'s "RED → GREEN") is posted by a completely separate workflow that tracks gate
  *state*, cites the sha that fixed it (not the one that broke it), and never references the
  original failing alert.

  Fixed the highest-value pair (`notify-qg-fail` CRITICAL <-> `notify-qg-recovered` GREEN, both in
  `unified-trading-ci/.github/workflows/python-quality-gates-v2.yml`) same-day:
  `record_decide` already reads+writes one Firestore doc (`qg_last_conclusion/{repo}:{branch}`)
  per run to compute the existing `recovered` flag — extended that doc with a `streak_start_sha`
  field: the sha that began the CURRENT run of same-verdict results on this branch, preserved
  across consecutive same-verdict runs, re-seeded the instant the verdict flips. `notify-qg-fail`
  now cites it as `· incident since \`<sha>\`` and `notify-qg-recovered` cites the just-resolved
  streak's start the same way (`(incident since \`<sha>\`)`) — both messages about one incident now
  carry the identical, greppable identifier, and it works uniformly for BOTH the LDR-push and
  promote-PR paths (one mechanism, not two). Shipped `unified-trading-ci@7000ac0` via direct push
  (`.github/**` carve-out, no quickmerge tooling in this small repo).
status: open
resolved_by:
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-ci, unified-trading-pm]
scope: [engineer, admin]
tags: [ci-alerting, slack, observability, ci-reconcile]
related:
  [
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /codex/04-architecture/ci-alerting.md,
    /cursor-configs/skills/ci-reconcile/SKILL.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-20"
parent_epic: ci_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.36
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    unified-trading-ci/.github/workflows/python-quality-gates-v2.yml,
    .github/workflows/ldr-to-main-promote.yml,
    .github/workflows/ldr-ci-monitor.yml,
    /codex/04-architecture/ci-alerting.md,
  ]
source: >-
  Direct operator feedback during a long `/autonomous` CI-alert-debounce session (2026-08-15/16) —
  the operator was reading the raw `#ci-failures` channel and could not tell which resolution post
  matched which failure post.
---

# CI-alert failure→resolution linkage

## Todos

- [x] [SCRIPT] P2. **Link `notify-qg-fail` (CRITICAL) and `notify-qg-recovered` (GREEN) by a shared
      `streak_start_sha`** — extended the existing `qg_last_conclusion` Firestore doc write in
      `record_decide` (unified-trading-ci's `python-quality-gates-v2.yml`) with a `streak_start_sha`
      field, threaded it through as new `quality-gates-v2` job outputs
      (`current_streak_start_sha`, `resolved_streak_start_sha`), and cited it in both alert
      messages. Covers both the LDR-push and promote-PR paths with one mechanism. **DONE
      2026-08-16** — shipped `unified-trading-ci@7000ac0`, YAML-validated
      (`python3 -c "import yaml; yaml.safe_load(...)"`) before push. Not yet observed live in
      Slack (no fresh failure→recovery cycle since shipping) — re-verify against a real incident
      the next time one occurs, and correct this doc if the actual posted text doesn't match what
      was intended.
- [ ] [BACKEND] P2. **Extend the same linkage to `ldr-to-main-promote.yml`'s drain-bot messages**
      ("closed promote PR(s) #N as superseded... fresh promote PR is #N+1"). These already form an
      implicit PR-number chain but never state "this resolves CRITICAL for incident since `<sha>`"
      — consider having the drain bot read the same `qg_last_conclusion` doc (or accept a passed
      streak-start sha) and append it, so a reader doesn't have to separately know that a
      PR-number chain and a sha-identity chain are two different things describing the same
      incident. **Done when**: a superseded-PR INFO post visibly cites the same
      `current_streak_start_sha` a corresponding `notify-qg-fail` CRITICAL used, when one exists.
- [ ] [BACKEND] P3. **Consider whether `ldr-ci-monitor.yml`'s RED→GREEN state-transition posts
      should also cite `streak_start_sha`** (or the sha that went red) instead of only the
      recovering sha — this is a separate, LDR-branch-health-focused monitor (not per-run QG
      alerts), lower priority since it's already a distinct, understood signal class, but still
      contributes to the "which resolution matches which failure" confusion the operator
      originally flagged. **Done when**: the operator confirms whether this is worth the added
      complexity, or explicitly rules it out of scope (LDR-branch-health is intentionally a
      coarser signal than per-run QG alerts).

## Progress Log

- 2026-08-16 (this session): filed after direct operator feedback; implemented and shipped the P2
  Todo 1 fix same-day (`unified-trading-ci@7000ac0`). Todos 2-3 are real follow-up scope,
  deliberately not attempted in the same pass — `ldr-to-main-promote.yml` lives in a different,
  currently much busier repo (`unified-trading-pm`, extreme concurrent-session contention measured
  earlier this session), and touching a fleet-wide promotion workflow under those conditions late
  in an already eventful session was judged not worth the risk. Left as tracked, scoped follow-up
  work rather than attempted blind.

- **context-scout 2026-08-17**: refreshed context_scope (4 entries) -- added `/codex/04-architecture/ci-alerting.md`,
  the SSOT this doc's own `related:` field already cited but its context_scope hadn't yet surfaced.

**na-eligibility-audit 2026-08-18** (ci tranche): KEEP-NA, valid. 2 open items: todo 2 ([BACKEND] P2, extend the
streak_start_sha linkage to ldr-to-main-promote.yml's drain-bot messages) reads bounded and was already independently
conflict-checked clear by `ag_closeout_audit_ci_parked_2026_08_16.md` ("ready to extract into batch16 whenever one is
next drafted... or let the operator decide to add it to batch15 directly if they want it sooner") — respecting that
standing recommendation rather than unilaterally drafting `batch16` now: `ci_satellite_ao_dispatch_batch15_2026_08_16.md`
independently re-checked today, still has ~14 of 25 todos open (not meaningfully drained), so the iterative-drain
condition that recommendation was gated on has not yet been met. Todo 3 ([BACKEND] P3, "consider whether
ldr-ci-monitor.yml... should also cite streak_start_sha") is explicitly operator-gated ("Done when: the operator
confirms whether this is worth the added complexity"). Tagged todo 2 `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` (ready,
deferred on timing) and todo 3 `OPERATOR_QUESTION`. Doc stays NA; no extraction this pass.
- **context-scout 2026-08-20**: refreshed context_scope (4 entries) — the two workflow files still open, the shipped
  QG workflow, and the ci-alerting SSOT all resolve.
