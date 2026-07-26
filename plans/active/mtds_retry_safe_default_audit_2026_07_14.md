---
doc_type: plan
title:
  MTDS retry_safe convention — pin the `else False` unclassified-default with a QG lint + codex SSOT (audit itself
  completed 2026-07-14)
summary:
  Follow-up to issues/mtds_perp_funding_backfill_hang_2026_07_14.md. The ~70-site audit this plan was originally sized
  for completed concurrently while it was being authored — market-tick-data-service@f82f29c1 (slot-8) classified all 70
  `classification.retry_safe if classification is not None else True` sites (68 log-only → standardized to the safe
  `else False` convention; 2 live-gating → fixed by market-tick-data-service@b8218f8a, slot-4, status-based 429/5xx
  fail-fast). What remains is pinning the convention so it cannot silently regress — a QG lint banning the `else True`
  fallback idiom (repo is at 2 deliberate residual sites, see body), a decision on those 2 residual transient-path
  sites, and the codex SSOT update documenting the convention in shard-level-failure-isolation.md.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [retry, error-classification, venue-error-map, adapters, qg-lint, fail-fast, mtds, convention]
related: [issues/mtds_perp_funding_backfill_hang_2026_07_14.md, issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md]
created: 2026-07-14
last_updated: 2026-07-14
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  "issues/mtds_perp_funding_backfill_hang_2026_07_14.md P3 audit-scope todo (slot-14 grep, 2026-07-14). The audit itself
  shipped concurrently (mtds@f82f29c1 + mtds@b8218f8a) while this plan was being authored — scope reduced to the
  unshipped remainder (QG lint + residual-site decision + codex SSOT). See Progress Log."
drift_direction: advance-code
---

# MTDS retry_safe convention — QG lint + codex SSOT (post-audit remainder)

> **Track note (authoring decision, 2026-07-14)**: authored as a LOCAL/human plan (`assigned_vm: NA`,
> `execution_scope: local-only`) — the documented DEFAULT per `plans/active/task_template.md` §1 and the CLAUDE.md "Plan
> destination — ASK BEFORE CREATING" hard rule; the operator is away and did not specify AO-dispatch. To hand this to
> the fleet later, flip `assigned_vm: planning` + `execution_scope: orchestrator-agent` (todos below already honour the
> AO 10–20 cap and `[TAG]` format).

## Context — what already shipped (do NOT redo)

`unified_api_contracts.classify_venue_error(venue, token)` returns `None` for any venue absent from `VENUE_ERROR_MAP`;
the historical MTDS idiom defaulted that unclassified case to `retry_safe = True`, which made permanent HTTP statuses
(404/400/403) retry up to `_MAX_RETRIES` for unregistered venues — the bug class behind the kalshi_perp VM-"hang"
(parent issue doc, fixed at mtds@5a163d02/56efdd7d).

Shipped under the parent issue doc's todos (all flipped there with evidence):

- **mtds@b8218f8a** (slot-4) — the 2 live-gating sites (`onchain/glassnode.py::_get`,
  `onchain/helius_solana.py::_rpc_call`, plus latent `::get_enhanced_transactions`) now branch on
  `aiohttp.ClientResponseError.status` via a shared per-module `_handle_response_error` helper (retry ONLY
  `{429, 500, 502, 503, 504}`, fail fast otherwise) BEFORE consulting `classify_venue_error`; regression tests mirror
  `test_non_retryable_status_fails_fast` (mtds@5a163d02).
- **mtds@f82f29c1** (slot-8) — full 70-site audit: 68/70 sites are pure `log_event` observability metadata before an
  unconditional raise (or log-and-continue), all standardized to the safe `else False` convention (the
  `defi/utils.py:80` / `prediction/kalshi_adapter.py:403` / `cli/handlers/_defi_manifest.py:698` /
  `prediction/polymarket_adapter.py:510` precedent).

**Residual state at HEAD (verified 2026-07-14, post-f82f29c1)**:
`grep -rn "classification.retry_safe if classification is not None else True" market_tick_data_service/` → exactly **2
hits** — `onchain/glassnode.py` and `onchain/helius_solana.py`, both on the **non-status exception path only**
(`aiohttp.ClientError` connection failures / `asyncio.TimeoutError`), where the permanent-status class is already
intercepted by `_handle_response_error` in the branch above. Retrying transient-by-nature network errors is defensible,
but these 2 sites are exactly what an idiom-lint would flag — they need an explicit decision (todo 2).

## Codex SSOTs

- `/codex/04-architecture/shard-level-failure-isolation.md` — classify via UAC `classify_venue_error()`; this plan adds
  the unclassified-default + status-branch convention to it (todo 4).
- `/codex/06-coding-standards/quality-gates.md` — QG structure for the new lint step (todo 1).

## Todos

- [ ] [BACKEND] P3. Add a QG lint step to `market-tick-data-service/scripts/quality-gates.sh` (repo-local, next to the
      existing 5.90-5.93 steps) banning the unsafe fallback idioms
      `classification.retry_safe if classification is not None else True` and `retry_safe if classification else True`
      in `market_tick_data_service/` — ratchet baseline = the decided residual count from todo 2 (0 if flipped, 2 if
      whitelisted-by-comment), failing on any INCREASE. Repo: `market-tick-data-service`.
- [ ] [BACKEND] P3. Decide + implement the 2 residual non-status-path sites (`glassnode.py` `_get` ClientError/Timeout
      branch, `helius_solana.py` `_rpc_call` same): either (a) flip to `else False` for full convention consistency
      (accepting fail-fast on first timeout for unregistered venues — check backfill impact first: a single flaky
      timeout would then fail the metric/method fetch immediately), or (b) keep `else True` for the transient-only error
      class with an explicit `# lint-allow` comment + lint whitelist, documenting WHY the transient path may default to
      retry. Record the decision rationale in this plan's Progress Log. Repo: `market-tick-data-service`.
- [x] [BACKEND] P3. Evaluate generalizing the lint into the shared PM `scripts/quality-gates-base/base-service.sh`
      codex-compliance section (fires for every repo consuming UAC `classify_venue_error`) — implement if trivially
      portable (pure `rg` step, no per-repo state); otherwise record why repo-local is the right home. Repos:
      `unified-trading-pm`, `market-tick-data-service`. ✅ DONE — trivially portable (pure `rg`, no per-repo state), so
      the fleet-wide home won over a repo-local duplicate. STEP 5.104 added, ratchet baseline=2 (the 2 annotated
      `# QG-allow: retry-safe` residual sites), fails on any new unmarked or unbaselined site.
- [x] [BACKEND] P3. Codex SSOT update — add the finalized convention to
      `/codex/04-architecture/shard-level-failure-isolation.md`: (1) unclassified venue error → `retry_safe = False`
      (never default-retry unknowns); (2) unregistered-venue HTTP errors → branch on status (retry only 429/5xx) BEFORE
      consulting the classifier; (3) cross-link the QG lint + the two fix commits as precedent. Repo:
      `unified-trading-pm`. ✅ DONE — all 3 sub-points added under a new "`classify_venue_error()` unclassified-default
      convention (retry_safe)" section, cross-linked to mtds@b8218f8a/f82f29c1/0041a8a6 + this plan + the parent
      incident doc.
- [ ] [BACKEND] P3. Closeout — verify the parent issue doc `issues/mtds_perp_funding_backfill_hang_2026_07_14.md` has no
      remaining open todos, set its `resolved_by:` to this plan + the fix shas, and run the issue-doc lifecycle
      (resolve/archive per `codex/11-project-management/`). Repo: `unified-trading-pm`.

## Progress Log

- 2026-07-14 — Plan authored from the parent issue doc's P3 audit-scope todo by the dispatched P1-fix agent. Mid-task
  reconciliation — the P1 fix AND the audit both shipped concurrently in other slots (mtds@b8218f8a slot-4 at 18:23Z,
  mtds@f82f29c1 slot-8 at 19:03Z; both verified ancestors of origin/live-defi-rollout by content, both flipped in the
  parent issue doc at PM@374acb516 / PM@fdc0cd1c1). This agent's duplicate working-tree fix was discarded in favor of
  the shipped equivalent (autostash-conflict resolution, WIP retained in the slot's git stash as `autostash`); plan
  scope reduced from "run the audit" to the unshipped remainder above. Residual `else True` count at HEAD verified = 2
  (non-status transient paths only); `else False` sites = 73.
- 2026-07-26 — Found this plan's todos 3-4 (lint generalization + codex SSOT update) sitting complete but uncommitted in
  the working tree (stranded, no session record of who wrote them — likely an earlier slot's WIP from the same
  2026-07-14 dispatch window that never got shipped). Verified before landing: bash syntax clean
  (`bash -n scripts/quality-gates-base/base-service.sh`), STEP 5.104's ratchet baseline (2) matches the 2 real annotated
  `# QG-allow: retry-safe` sites at HEAD, and both cited fix commits (`mtds@b8218f8a`, `mtds@f82f29c1`) plus the
  residual-annotation commit (`mtds@0041a8a6`) are real, already-shipped ancestors. Flipped both todos, shipping now.
  Todos 1-2 (repo-local MTDS lint, residual-site decision) and 5 (parent-issue closeout) remain open — not addressed by
  this uncommitted diff.
