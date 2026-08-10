---
doc_type: issue
title: >-
  execution-service LDR carries 7 strict-quickmerge provenance bypasses (source changed without Quickmerge trailer) —
  will block the next LDR→main promote PR on quickmerge-provenance
summary: >-
  Found during the 2026-08-10 ci_reconciler fleet sweep (§4 provenance-gate scan). `check_strict_quickmerge.py --range
  origin/main..origin/live-defi-rollout --block` flags 7 commits on execution-service live-defi-rollout whose source
  files changed WITHOUT a `Quickmerge:` trailer (or carve-out). execution-service main was last updated
  2026-08-10T18:35Z; the 7 bypasses sit in `origin/main..origin/live-defi-rollout`, so the next promote PR for
  execution-service (LDR content ≠ main) will be provenance-blocked and left unarmed by `ldr_to_main_fleet_promote.sh`
  (which auto-dispatches a `provenance_blocked` escalation). Bulk-blessing is a judgment call per the ci-reconcile
  skill's size/authorship gate (7 > 5, multi-subsystem, multi-agent) — this doc records the backlog for an operator
  decision; it is NOT a same-run bulk-bless.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [provenance, quickmerge, promotion, ci-cd, ldr, strict-quickmerge]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md,
  ]
created: "2026-08-10"
author: ci_reconciler slot-27
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: operator-gated
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role:
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source: [ci_reconciler sweep 2026-08-10, dispatch agt-431623]
---

# execution-service LDR provenance-bypass backlog

## The 7 bypasses (in `origin/main..origin/live-defi-rollout`)

1. `da580391` feat(credentials): wire Bybit trade-scope secret with safe fallback
2. `bfb135c1` fix(credentials): fix venue trade-credential loading + Hyperliquid CCXT auth
3. `24b47225` fix(credentials): fix TrancheRouter secret resolution to match live GCP naming
4. `da10ddb4` fix(manifest): thread available_at through ExecutionManifestRecorder.record_captured()
5. `24948952` fix(matching-engine): pop price from kwargs in solana snapshot fallback
6. `3208ec84` refactor(codex): shave the last 2 near-budget methods
7. `1e8e7608` refactor(codex): decompose 26 oversized functions/methods below line budget

All are legitimate agent-authored code changes that reached LDR without the `Quickmerge:` trailer (raw/other-path push,
or the trailer was lost). `check_strict_quickmerge.py --block` exits 1 on execution-service; exit 0 (clean) after
re-provenancing. Files touched span credentials, manifest recording, matching-engine, and adapters — multi-subsystem.

## Why it matters

`quickmerge-provenance` is one of the THREE LDR→main promote-PR gates (CLAUDE.md Git discipline). When the next
fleet-promote tick creates execution-service's promote PR (LDR content ≠ main), `ldr_to_main_fleet_promote.sh` runs its
provenance probe, finds the bypasses, posts `<!-- promote:provenance-blocked -->`, leaves the PR unarmed, and dispatches
`escalate-to-orchestrator` (wall_type provenance_blocked). Promotion stalls until resolved.

## Resolution options (operator decision)

- **Re-ship each individually** through `quickmerge --agent --files <paths>` — clean but 7 round-trips.
- **Reprovenance** the mid-history commits via `scripts/cicd/reprovenance_bypass.sh <sha> --push` (creates an empty
  `Reprovenance: <sha>` blessing commit; the tool verified clean on mtds `064f872a` this run). Works because
  `check_strict_quickmerge.py` forgives a bypass whose full sha is named in a provenanced commit.
- **Bulk-bless** — NOT done here: 7 > 5 and multi-subsystem, so per the ci-reconcile skill's size/authorship gate this
  is a judgment call, not a mechanical fix.

## Verified state

- `check_strict_quickmerge.py --range origin/main..origin/live-defi-rollout --block` on execution-service: exit 1, 7
  sites (2026-08-10 ~18:50Z).
- Same check on `market-tick-data-service`: was 1 site (`064f872a`), now clean after
  `reprovenance_bypass.sh 064f872a --push` landed `c20ed049` (2026-08-10 ~18:52Z).
