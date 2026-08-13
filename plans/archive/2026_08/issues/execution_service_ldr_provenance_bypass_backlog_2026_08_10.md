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
status: resolved
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
  "Reprovenance path per operator ruling 2026-08-12 (interactive session, slot-3) on this doc's own 'Resolution options
  (operator decision)' section in execution_service_ldr_provenance_bypass_backlog_2026_08_10.md. Ran
  `scripts/cicd/reprovenance_bypass.sh <sha> --push` for all 7 bypassed shas on execution-service live-defi-rollout:
  da580391→d473a647, bfb135c1→6350eca4, 24b47225→46c35e0b, da10ddb4→020865d8, 24948952→ddee4aea, 3208ec84→e896fc08,
  1e8e7608→5d84fec3 (empty `Reprovenance:`+`Quickmerge: agent` blessing commits, one per bypass, per-commit
  dep-alignment gate passed each time). Verified: `check_strict_quickmerge.py --range
  origin/main..origin/live-defi-rollout --block` now exits 0 (was exit 1 / 7 sites before). Checked the live escalation
  queue (`GET /api/escalations/active` via SSM) — 13 active escalations fleet-wide, none referencing execution-service
  or provenance, and no open execution-service promote PR exists — so this backlog was cleared pre-emptively, before the
  fleet-promote tick ever produced a `provenance_blocked` wall."
source: [ci_reconciler sweep 2026-08-10, dispatch agt-431623]
---

# execution-service LDR provenance-bypass backlog

> **ARCHIVED (2026-08-12)** — resolved via the reprovenance path, per operator ruling (interactive, slot-3). All 7
> bypassed shas reprovenanced on execution-service `live-defi-rollout` (blessing commits `d473a647`, `6350eca4`,
> `46c35e0b`, `020865d8`, `ddee4aea`, `e896fc08`, `5d84fec3`);
> `check_strict_quickmerge.py --range origin/main..origin/live-defi-rollout --block` now exits 0 clean. Successor: none
> (self-contained fix; no follow-up work).

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

## Todos

- [x] ✅ [OPERATOR] P2. Operator ruled (2026-08-12, interactive): use the **reprovenance** path. Ran
      `scripts/cicd/reprovenance_bypass.sh <sha> --push` for each of the 7 bypassed shas on execution-service
      live-defi-rollout, verifying `check_strict_quickmerge.py --range origin/main..origin/live-defi-rollout --block`
      after each. Final state: exit 0 (clean), was exit 1/7 sites. See `resolved_by` for the sha→blessing-commit
      mapping. — execution-service (7 reprovenance commits, see Progress Log).

## Verified state

- `check_strict_quickmerge.py --range origin/main..origin/live-defi-rollout --block` on execution-service: exit 1, 7
  sites (2026-08-10 ~18:50Z).
- Same check on `market-tick-data-service`: was 1 site (`064f872a`), now clean after
  `reprovenance_bypass.sh 064f872a --push` landed `c20ed049` (2026-08-10 ~18:52Z).
- **2026-08-12**: same check on execution-service now exit 0 (clean) after all 7 shas reprovenanced — see Progress Log.

## Progress Log

- **2026-08-12** (slot-3, interactive): operator ruled use the reprovenance path (not re-ship, not bulk-bless).
  Pre-flight: confirmed execution-service checkout on `live-defi-rollout`, up to date with `origin/live-defi-rollout`,
  no dirty tracked changes (two pre-existing untracked files unrelated to this work left alone). Confirmed the live
  `check_strict_quickmerge.py --range origin/main..origin/live-defi-rollout --block` output matched the doc's 7 shas
  exactly (same shas, same subject lines) before touching anything. Ran
  `scripts/cicd/reprovenance_bypass.sh <sha> --push` for each of the 7, in order, each one gated on a fresh
  dep-alignment check and each push confirmed by the tool's own post-push strict-quickmerge probe:
  - `da580391` → blessing commit `d473a647751be887e267ebcbbcbc29b0ecf18570`
  - `bfb135c1` → blessing commit `6350eca4c9100a27adcba30a517490ffe5e3ac73`
  - `24b47225` → blessing commit `46c35e0bf8e93b2f0d61a772d40515bfcf934a9a`
  - `da10ddb4` → blessing commit `020865d879ddb2bbb910ab5fa7d602cd269dcd0a`
  - `24948952` → blessing commit `ddee4aea62dbc94435e7d3e62b2c0db459336d66`
  - `3208ec84` → blessing commit `e896fc0860ce638270016409be3ecf9ec782e101`
  - `1e8e7608` → blessing commit `5d84fec37c75c021492a74d176676b7f7282bf7b`

  Final full-range check after all 7: `check_strict_quickmerge.py --range origin/main..origin/live-defi-rollout --block`
  → exit 0, clean. Checked whether an actual `provenance_blocked` escalation existed to clear: no open execution-service
  promote PR (`gh pr list` empty), and the live escalation queue (`GET /api/escalations/active` via SSM against the
  orchestrator VM) shows 13 active escalations fleet-wide, none mentioning execution-service or provenance — so this
  backlog was resolved pre-emptively, before the fleet-promote tick ever produced the wall the doc describes. Nothing
  left to re-check post-hoc; the next fleet-promote tick for execution-service will now find
  `origin/main..origin/live-defi-rollout` provenance-clean.
