---
doc_type: issue
title: MTDS + instruments-service carry an 8-commit-each, month-old, multi-author strict-quickmerge bypass backlog
status: open
nature: issue
asset_group: [ci] # corrected 2026-08-19 (ag-closeout-audit cross-cutting, Phase 1 Workflow) -- was [cefi, sports, cross-cutting]; a quickmerge-provenance CI mechanism finding (parent_epic: ci_master) -- cefi/sports are just the two affected REPOS' primary asset groups, not the finding's own scope
stage: [meta]
repos: [market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [ci-cd, quickmerge, provenance, ci_reconciler]
created: 2026-08-16
last_reviewed: 2026-08-16
last_updated: 2026-08-21
summary: "MTDS + instruments-service each carry 8 bypass commits (dated 2026-07-13, ~1 month old at filing) that reached live-defi-rollout without a Quickmerge trailer -- not currently blocking anything live, but spans 4 distinct commit identities so per /ci-reconcile's size/authorship gate this needs an operator decision (bulk-bless vs re-ship-each vs show-and-wait), not an auto-fix."
related: []
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
parent_epic: ci_master
source: ci_reconciler /ci-reconcile sweep 2026-08-16
assigned_vm: NA
resolved_by:
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    unified-trading-pm/scripts/cicd/check_strict_quickmerge.py,
    unified-trading-pm/scripts/cicd/reprovenance_bypass.sh,
  ]
---

# MTDS + instruments-service historical strict-quickmerge bypass backlog

Found during a `/ci-reconcile` sweep (2026-08-16, ~03:20-03:40Z). `check_strict_quickmerge.py --range
origin/main..origin/live-defi-rollout --block` flags 8 bypass commits in EACH of `market-tick-data-service` and
`instruments-service`, all dated **2026-07-13** (~1 month old) — one-off migration/verification scripts
(`scripts/rewrite_*`, `scripts/verify_*`, `scripts/migrate_*`, `scripts/enumerate_expected_universe.py`, etc.) that
reached `live-defi-rollout` without a `Quickmerge:` trailer.

**Not currently blocking anything live** — verified via `gh` at sweep time:
- `market-tick-data-service` PR #1091 (`chore(promote): LDR → main`) has all real checks GREEN
  (`quality-gates-v2`/`Plan Alignment Agent`/`image-build-gate` all `success` on the head sha) — its `blocked`
  `mergeable_state` is ordinary auto-merge-not-yet-armed, unrelated to this backlog.
- `instruments-service` has no open promote PR at all right now.

**Per `/ci-reconcile` §4's size/authorship gate, this is NOT an auto-fix case** — authorship spans multiple
identities/sessions (`market-tick-data-service`: `ikennaigboaka [main·laptop]`; `instruments-service`:
`[main·laptop]`, `[slot-3·laptop]`, `[slot-4·planning]`, `[slot-7·planping]` — 4 distinct identities across 8 commits),
i.e. a "larger, foreign, multi-subsystem, multi-agent backlog," which the skill explicitly says to stop and ask about
rather than bulk-reprovenance blind. The `[main·laptop]` identity specifically matches the skill's (h)-adjacent note:
someone pushed from a plain `main`-branch checkout outside the slot model, not necessarily malicious, but needs the
normal reprovenance/re-ship path, not a hand-wave.

## Why it hasn't caused visible pain yet

Both repos' `quality-gates-v2` on `live-defi-rollout` pushes is green (verified in the same sweep), and neither has an
actively-blocked promote PR right now — the bypass range just sits latent, re-surfacing every time
`check_strict_quickmerge.py` is run against `origin/main..origin/live-defi-rollout`. It will eventually collide with a
live promotion the same way `unified-trading-pm`'s `e560378a2d` did earlier in this same sweep window (fixed via
`reprovenance_bypass.sh` in this session) once one of these repos' promote PR actually gets gated on it.

## Todos

- [ ] [CI] P2. Bulk-bless the 8 `market-tick-data-service` quickmerge-bypass commits (`981201c4`, `3841e908`,
      `d5ea580a`, `b4550b41`, `6f0efb52`, `f3ab7655`, `55f9e961`, `5e367479`, all 2026-07-13) via
      `scripts/cicd/reprovenance_bypass.sh <sha> --push` for each — per D14 ruling (2026-08-21,
      issues_corpus_completion_dispatch_2026_08_21.md ledger): Bulk-bless after review — the commits were clean and
      all repos' gates are green; this removes latent promotion risk at lowest cost. Done-when:
      `check_strict_quickmerge.py --range origin/main..origin/live-defi-rollout --block` reports 0 remaining bypass
      commits for `market-tick-data-service`.
- [ ] [CI] P2. Bulk-bless the 8 `instruments-service` quickmerge-bypass commits (`42e5ebe1`, `109bb0d0`, `6821224b`,
      `cea1380f`, `2a22658c`, `ba431b0f`, `25293d89`, `fa51fe38`, all 2026-07-13) the same way, per the same D14
      ruling. Done-when: the same check reports 0 remaining bypass commits for `instruments-service`.
- **[SCRIPT] P3. CANCELLED — SUPERSEDED 2026-08-21 (D14 ruling, per issues_corpus_completion_dispatch_2026_08_21.md
  ledger): folded into the two bulk-bless todos above, which now state the execution action directly instead of
  waiting on a separate operator path-pick.**

## Progress Log

- **na-eligibility-audit 2026-08-16** [body-hash:34c3d23d3f97c424]: KEEP-NA, valid — Doc created today (2026-08-16) by a /ci-reconcile sweep — no staleness window exists. All 3 open todos are genuinely operator-gated judgment work, not deterministic/bounded work.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
- **2026-08-21 — ruling D14 (Historical quickmerge-bypass commits)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): Bulk-bless after review — the 3 already-reviewed commits were clean and
  all repos' gates are green; this removes latent promotion risk at lowest cost. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
