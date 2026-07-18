---
doc_type: issue
title:
  One agent's invalid frontmatter on the shared branch blocks EVERY agent's quality gate, and the sanctioned remedy
  refuses to touch a foreign-dirty file — so only the owner can clear it
summary:
  Measured 2026-07-18 ~21:19-22:26 UTC. slot-1 pushed
  plans/active/issues/launcher_gcloud_continuation_broken_by_disk_sweep_2026_07_18.md to live-defi-rollout with four
  invalid frontmatter enums (status:fixing, nature:bug, asset_group:infra, stage:infra). check_frontmatter_schema runs
  corpus-wide as a post-gate check, so from that moment EVERY agent in EVERY clone failed `quality-gates.sh` on a file
  none of them owned or touched - shipping was blocked fleet-wide for ~55 minutes until the owner returned and corrected
  it. The documented remedy, `seed_frontmatter.py --apply <path>`, refuses with "skipped (foreign-dirty)" precisely
  because the file has another agent's uncommitted edits, so no other agent can legitimately clear the block. That guard
  is CORRECT and should stay - when I attempted a precedent-based normalization by hand, my values would have been wrong
  on 2 of 4 fields (I chose status:open / asset_group:[infrastructure]; the owner chose status:resolved /
  asset_group:[cross-cutting]). The gap is that a corpus-wide blocking check has no owner-scoped fallback - correctness
  of the guard and liveness of the fleet are in direct tension.
status: open
resolved_by:
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cicd, quality-gates, frontmatter, multi-agent, shipping, deadlock, plan-hygiene]
related: [quickmerge_sentinel_invalidated_by_its_own_autopull_2026_07_18.md]
created: 2026-07-18
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: devops
drift_direction: none
locked_by:
source: measured during the 2026-07-18 CI-failure sweep while shipping f1ac557bb
depends_on: []
---

# Foreign-dirty frontmatter blocks the whole fleet's gate

## What happened

| time (UTC) | event                                                                                                      |
| ---------- | ---------------------------------------------------------------------------------------------------------- |
| 21:19      | slot-1 commits + pushes the doc with `status: fixing`, `nature: bug`, `asset_group: infra`, `stage: infra` |
| 21:19+     | every `quality-gates.sh` run in every clone fails `frontmatter-schema` on that one file                    |
| 21:31      | my ship attempt blocked; peer file mtime 0m → PROTECT per the liveness rule                                |
| ~22:01     | 30-minute watcher expires, doc still invalid, slot-1 quiet — claim now reads as dead                       |
| 22:05      | I normalize the four enums by precedent; `seed_frontmatter.py --apply` refuses: `skipped (foreign-dirty)`  |
| 22:06      | I revert byte-identically and stand down                                                                   |
| 22:26      | slot-1 returns and fixes it properly; gate clears; my change ships as `f1ac557bb`                          |

Total fleet-wide shipping block: **~55 minutes**, caused by four enum values in a doc nobody else touched.

## Why the guard is right

`seed_frontmatter.py`'s foreign-dirty refusal is not the bug — it is the thing that stopped me making it worse. My
hand-normalization would have committed the owner's doc with **two of four fields wrong**:

| field         | my precedent-based guess | owner's actual value  |
| ------------- | ------------------------ | --------------------- |
| `status`      | `open`                   | **`resolved`**        |
| `asset_group` | `[infrastructure]`       | **`[cross-cutting]`** |
| `nature`      | `issue`                  | `issue` ✓             |
| `stage`       | `[meta]`                 | `[meta]` ✓            |

`status` in particular is semantic, not derivable — only the author knew the issue was already fixed.

## The real gap

A **corpus-wide** blocking check has no **owner-scoped** fallback. The check is right to be corpus-wide (that is what
keeps the plan corpus honest), and the remedy is right to refuse foreign-dirty files, but together they mean a single
agent's in-progress doc can freeze every other agent's ship path with no legitimate escape.

## Options (not chosen)

1. **Scope the post-gate frontmatter check to the docs in YOUR changeset** (staged + committed-but-unpushed), the way
   pre-push guard [2] already does. A corpus-wide sweep still runs in CI's lint-codex slice, so nothing stops being
   enforced — it just stops blocking unrelated agents locally. Closest to how the pre-push guard already reasons.
2. **Downgrade corpus-wide violations on files you do not own to a WARNING locally**, keeping them blocking in CI.
   Preserves the signal, removes the cross-agent block.
3. **Make the pre-COMMIT hook catch it at the source.** It already runs `run_hygiene_sweep.sh --precommit`; the doc
   still landed, so either the hook was bypassed or the sweep did not cover these keys — worth confirming which before
   choosing 1 or 2, since fixing the source would make the rest moot.
4. **Do nothing** — rely on owners returning promptly. Cost measured tonight: ~55 min of fleet-wide block.

## Recommendation

Establish (3) first — if the doc reached the shared branch through a bypass, that is the actual defect and the cheapest
fix. Otherwise (1), which mirrors an existing, already-accepted pattern in this repo rather than inventing a new one.
