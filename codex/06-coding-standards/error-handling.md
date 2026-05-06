---
scope: [engineer]
---

<!-- POST_PLAN_BANNER_2026_05_06 -->

> **POST-PLAN REALITY (2026-05-06)** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md)
> BEFORE making code or doc changes informed by this doc. This doc is partially stale: doesn't list the three-category
> empty-output decision tree (path A `record_empty` / path B `UpstreamTimestampBiasError` / path C
> `MalformedTickFieldError`). The post-plan-reality doc lists the 10 cross-cutting principles codified in workspace
> `CLAUDE.md` (live=batch, no double SSOT, three-category empty-output decision, cluster validation mandatory, per-row
> write-time `available_at`, prediction lifecycle timing, temporary state must have named successor, per-VM shard
> isolation, etc.) plus the active plans where the canonical post-plan reality is being implemented
> (`writegate_honest_coverage_endtoend_2026_05_06.plan.md`,
> `predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`). If this doc and the active plans
> disagree, the plans win. If you find a contradiction the plans don't address, flag to user — don't decide
> unilaterally.

# Error Handling

See 06-coding-standards/README.md.
