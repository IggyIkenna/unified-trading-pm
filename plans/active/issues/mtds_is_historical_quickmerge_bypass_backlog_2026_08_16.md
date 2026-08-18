---
doc_type: issue
title: MTDS + instruments-service carry an 8-commit-each, month-old, multi-author strict-quickmerge bypass backlog
status: open
nature: issue
asset_group: [cefi, sports, cross-cutting]
stage: [meta]
repos: [market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [ci-cd, quickmerge, provenance, ci_reconciler]
created: 2026-08-16
last_reviewed: 2026-08-16
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

- [ ] [OPERATOR] P2. Decide bulk-bless-after-review vs. re-ship-each-individually vs. show-and-wait for the 8
      `market-tick-data-service` bypass commits (`981201c4`, `3841e908`, `d5ea580a`, `b4550b41`, `6f0efb52`,
      `f3ab7655`, `55f9e961`, `5e367479`, all 2026-07-13) — per `/ci-reconcile` §4, this is a judgment call, not a
      mechanical fix.
- [ ] [OPERATOR] P2. Same decision for the 8 `instruments-service` bypass commits (`42e5ebe1`, `109bb0d0`, `6821224b`,
      `cea1380f`, `2a22658c`, `ba431b0f`, `25293d89`, `fa51fe38`, all 2026-07-13).
- [ ] [SCRIPT] P3. Once the operator picks a path, either reprovenance each commit via
      `scripts/cicd/reprovenance_bypass.sh <sha> --push` (bless path) or re-ship equivalent content via
      `quickmerge.sh --agent --files` (re-ship path) for whichever commits are approved.

## Progress Log

- **na-eligibility-audit 2026-08-16** [body-hash:34c3d23d3f97c424]: KEEP-NA, valid — Doc created today (2026-08-16) by a /ci-reconcile sweep — no staleness window exists. All 3 open todos are genuinely operator-gated judgment work, not deterministic/bounded work.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
