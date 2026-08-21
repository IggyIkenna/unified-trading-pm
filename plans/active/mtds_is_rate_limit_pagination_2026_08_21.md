---
doc_type: plan
title: MTDS + instruments-service — rate limiting and pagination (2026-08-21 operator directive)
summary: >-
  Builds per-tier token-bucket rate limiting and real opaque-cursor pagination on both services'
  external routers, closing the gap platform-external-api-walkthrough.html previously disclosed as
  absent/planned. instruments-service landed; market-tick-data-service is code-complete and gate-
  green but ship-held on a confirmed pre-existing, unrelated regression in a shared multi-lane slot.
  Split into its own doc because both natural homes (walkthrough_feedback_remediation_2026_08_21.md,
  code_readiness_t2_refdata_marketdata_2026_08_19.md) are at their 1000L hard line cap.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [external-api, rate-limiting, pagination, code-readiness, walkthrough]
related:
  [
    /plans/active/walkthrough_feedback_remediation_2026_08_21.md,
    /plans/active/code_readiness_t2_refdata_marketdata_2026_08_19.md,
  ]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: brand-new
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
locked_by:
locked_since:
context_scope:
  [
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/06-coding-standards/quality-gates.md,
    instruments-service/instruments_service/api/,
    market-tick-data-service/market_tick_data_service/api/,
  ]
supersedes:
superseded_by:
depends_on: [walkthrough_feedback_remediation_2026_08_21]
source: >-
  Operator directive 2026-08-21 (recorded in walkthrough_feedback_remediation_2026_08_21.md): the
  external API's rate limiting and pagination must be BUILT, not disclosed as absent. A proven
  token-bucket pattern already existed in the workspace (strategy-service's signal_broadcast rate
  limiter) — mirrored for mechanics only, no service→service import, each service's implementation
  kept local.
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
---

# MTDS + instruments-service — rate limiting and pagination

## Todos

- [x] ✅ [BACKEND] P0. **instruments-service — rate limiting + pagination.** Per-tier token-bucket
      rate limiter (`instruments_service/api/rate_limit.py`, keyed off
      `AuthContext.subscription_tier`, mirrors strategy-service's signal_broadcast `RateLimiter`
      mechanics as a fresh LOCAL implementation — no service→service import; internal/S2S callers
      bypass; HTTP 429 + `Retry-After` on exhaustion) wired into both `GET /v1/instruments` and
      `/bulk`. `GET /v1/instruments` gains an opaque continuation cursor beyond `limit`
      (`catalogue_query.query_instruments`'s new `offset`/`next_offset`, a `limit + 1` peek for an
      honest `truncated` — replacing the prior `len(rows) > limit or venues_scanned <
      len(shard_paths)` approximation, which could misreport `truncated: false` when a later shard
      was empty); `limit` semantics unchanged, `/bulk` stays the full-corpus path and does not
      paginate. Tests: `tests/unit/test_rate_limit.py` (per-tier bursts, internal bypass, per-org
      isolation, deterministic refill), `tests/unit/test_catalogue_query.py` (multi-page offset
      walk, exact-total non-truncation, offset-beyond-total, instrument_type-filter ordering),
      `tests/unit/test_external_router.py` additions (cursor round-trip, tamper/mismatch rejection,
      HTTP-level 429 + bulk-endpoint throttling — hardened to drain-until-a-429-is-observed rather
      than assume exact-burst-count exhaustion, since real wall-clock refill during sequential
      in-process HTTP round-trips made a fixed-count loop occasionally flaky).
      ✅ 2026-08-21 — **SHIPPED, instruments-service@c8c9c58b76** (`--isolated` ship — this checkout
      is a shared multi-lane slot; verified ancestor of `origin/live-defi-rollout`).
      `quality-gates.sh --no-fix` full green after `instruments-service@3dcee8d602` ("zero
      unresolved venue/data_type pairs", the registry lane's enumerator fix) landed and resolved 7
      pre-existing `options_chain`/`futures_chain` bundle-grouping test failures this session's
      earlier runs hit first — confirmed pre-existing and unrelated to this change via `git stash`
      isolation (byte-identical failure on a clean tree with zero of this session's changes
      present) before that fix landed, then re-confirmed resolved after. Also hit and cleanly
      resolved (kept the already-landed content, discarded the pre-format duplicate) a benign
      autostash conflict on `tests/unit/scripts/test_expected_universe_golden.py` during the
      post-fix `git pull --ff-only` — the SAME test method had been written into this shared
      checkout twice via two paths (the registry lane's isolated commit + a pre-format mirror left
      in this slot's shared working tree), not a real content conflict.
      `codex/14-customer-journeys/commercial-model/platform-api-reference.html` (§01 shared
      rate-limit tier table + §02 `cursor` param/errors/examples) and
      `platform-external-api-walkthrough.html` ("Rate limits and pagination — the built reality",
      replacing the prior "neither is built yet" disclosure) updated in the same pass.
- [ ] [BACKEND] P0. **market-tick-data-service — rate limiting + `delivery/batch` pagination
      cursor.** Same rate-limit mechanics as the instruments-service todo above, local
      implementation (`market_tick_data_service/api/rate_limit.py`), wired into all three external
      endpoints (`availability`, `delivery/batch`, `delivery/stream`). `delivery/batch`'s listing
      step gains a real opaque continuation cursor (base64 of the last-returned object's name; the
      storage client's own `start_offset` semantics — inclusive, so the boundary object is skipped
      on resume); `truncated` now also fires on hitting the raw-scan bound
      (`_LIST_MAX_OBJECTS_SCANNED`), not only the 200-object match cap — previously a listing that
      hit the scan bound first, before finding 200 matches, silently reported `truncated: false`.
      Tests: `tests/unit/api/test_rate_limit.py` (per-tier bursts, internal bypass, per-org
      isolation, deterministic refill), `tests/unit/api/test_external_router.py` additions
      (multi-page cursor walk, cursor-tamper rejection, the scan-cap-vs-match-cap truncation
      regression test, per-tier 429 + internal bypass — hardened the same drain-until-observed way
      as the instruments-service tests above).
      **Code complete, `quality-gates.sh --no-fix` fully green this session (11149 passed; only
      pre-existing, unrelated failures ever seen — see below) — SHIP HELD**, not code-incomplete:
      blocked purely by `quickmerge.sh`'s tree-wide re-gate hard-failing on an already-landed,
      confirmed-unrelated regression at `origin/live-defi-rollout@1e2baca8`:
      `tests/unit/test_pipeline_e2e_cefi_defi_canonical.py::test_defi_prefix_parser_handles_multi_hyphen_protocol_keys`
      — `_write_prefix_candidates` mis-splits a multi-hyphen DeFi venue/chain key (e.g.
      `SOLANA-NATIVE-SOLANA` does not produce `venue=SOLANA-NATIVE/chain=SOLANA/`). Confirmed via
      `git stash push -u` isolation against this checkout's exact HEAD (verified byte-identical to
      `origin/live-defi-rollout` via `git fetch` + `git rev-parse` at the time) that the failure is
      present with ZERO uncommitted changes from any lane — i.e. a real landed regression, not
      foreign shared-slot WIP bleeding into the test run (this shared slot separately also carries
      an unrelated, uncommitted DeFi-handlers lane's WIP —
      `dex_swaps_handler.py`/`eigenlayer_rewards_handler.py`/`flash_loan_events_handler.py`/
      `governance_events_handler.py`/`liquidation_events_handler.py`/`position_data_handler.py`/
      `staking_yields_handler.py` + tests — which is NOT the cause here, just co-resident noise,
      confirmed by the same isolation test). `quickmerge.sh` has no allowance for "pre-existing,
      confirmed-unrelated" — it re-gates the whole tree and hard-blocks regardless, so this repo
      cannot ship until the regression below is fixed. Follow-up todo tracks it; ship via
      `--isolated` the moment it's resolved (this checkout hosts multiple concurrent lanes — the
      shared tree will not go clean on its own).
- [ ] [BACKEND] P1. Fix market-tick-data-service's `_write_prefix_candidates` multi-hyphen DeFi
      venue/chain split regression, found while shipping the rate-limiting/pagination todo above —
      `tests/unit/test_pipeline_e2e_cefi_defi_canonical.py::test_defi_prefix_parser_handles_multi_hyphen_protocol_keys`
      fails on a clean `origin/live-defi-rollout@1e2baca8` tree (confirmed via `git stash`
      isolation against that exact commit; not caused by rate-limiting/pagination or by this
      checkout's other uncommitted lanes). Expected: a venue like `SOLANA-NATIVE-SOLANA` should
      split to `venue=SOLANA-NATIVE/chain=SOLANA/`. Blocks the P0 rate-limiting/pagination todo
      above from landing. Not attempted in this pass — unfamiliar, non-trivial DeFi venue/chain
      parsing logic, out of this task's own scope.

## Progress Log

- 2026-08-21 — instruments-service shipped (`instruments-service@c8c9c58b76`). market-tick-data-
  service code-complete and gate-green, ship held on the pre-existing `_write_prefix_candidates`
  regression above (not this work's fault) — will ship via `--isolated` once that lands.
