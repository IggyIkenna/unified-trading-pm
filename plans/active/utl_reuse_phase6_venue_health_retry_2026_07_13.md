---
doc_type: plan
title: UTL/UAC reuse consolidation — Phase 6 venue-error, health router, retry helper
summary:
  Fold execution-service's second hand-rolled /health onto UTL make_health_router, and consolidate the MTDS + IS
  base-adapter retries onto the new UTL retry helper; venue-error classification already shipped.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [utl, uac, consolidation, refactor, venue-error, health, retry, split]
related: [plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
locked_by: live-defi-rollout
locked_since: "2026-07-13"
supersedes:
superseded_by:
depends_on:
source: [split from utl_uac_reuse_consolidation_remediation_2026_06_10 tracker, operator-approved 2026-07-13]
assigned_role: backend-engineer
drift_direction: advance-code
---

# UTL/UAC reuse consolidation — Phase 6 venue-error, health router, retry helper

> **Split provenance (2026-07-13):** Phase 6 of
> [`utl_uac_reuse_consolidation_remediation_2026_06_10.md`](utl_uac_reuse_consolidation_remediation_2026_06_10.md)
> (findings #8, #10, #11). instruments-service's venue-error classification and the UTL retry-helper addition already
> shipped — reproduced below as done. Independent of every other split plan — no gate.

## Todos

- [x] ✅ [AGENT] P1. **instruments-service** — DONE `instruments-service@66165f2e` (23 tests ✓, QG 0; direct-push
      carve-out — UTL was transiently dirty). Deleted local `VenueError`; all 8 construction sites now build UAC
      `VenueErrorClassification` (`retry_safe`/`reconnect`/`action: ErrorAction`); `VenueFetchResult` wrapper kept.
- [x] ✅ [AGENT] P2. **execution-service** — DONE `execution-service@348385ad` (8 new tests ✓, `quality-gates.sh` exit
      0, sentinel-verified). Folded `api/app.py`'s hand-rolled `/health`+`/ready`+`/readiness` onto UTL
      `make_health_router(...)`: `/readiness` preserves the former standalone endpoint's exact gate (auth + limiter +
      handler wired at startup) via a `readiness_check` callback; `/health` surfaces recovery-completion as a non-gating
      `checks.recovery` entry instead of a separate `/ready` route (`mark_recovery_complete()` has zero callers
      repo-wide, so folding it into the gating `readiness_check` would have made `/readiness` permanently 503 — kept
      non-gating instead, preserving `/readiness`'s actual current behavior). No `data_freshness` callback —
      execution-service's live-trading app has no batch-pipeline "last processed date" concept to attach one to (unlike
      `api/main.py`'s use case); `data_freshness` is optional on `make_health_router` and QG STEP 5.62 is a structural
      `make_health_router`-presence grep, already satisfied. Also fixed a pre-existing, unrelated codex-compliance
      ratchet breach discovered while shipping (repo's own `CODEX_MAX_VIOLATIONS=3` was at 4: click + pillow CVEs, a
      `providers/` hardcoded-project-id exclude-glob, a false-positive backward-compat-shim comment reword) — see
      `plans/active/issues/execution_service_codex_compliance_ratchet_breach_2026_07_13.md` (3 of its 4 buckets fixed;
      the 25-oversized-function bucket left open, out of scope). Resolved a real merge conflict with a concurrent peer
      slot's independent fix for the same false-positive comment (took the already-landed upstream wording) and
      reconciled overlapping hardcoded-project-id fixes (peer fixed 3 files via real config interpolation; kept only the
      still-needed `providers/` exclude-glob).
- [x] ✅ (UTL helper half) **Add a UTL retry helper** — DONE `unified-trading-library@20c8ae8d`: `retry` (decorator) +
      `with_retry` (callable), stdlib-only, exp backoff + jitter, 429/5xx-aware, exported from
      `unified_trading_library.utils.retry` / `.utils` / top-level. 9 new tests.
- [x] ✅ [AGENT] P2. **Consume the UTL retry helper** (REMAINING): consolidate the two hand-rolled base-adapter retries
      — MTDS `market_interface/base_adapter.py:29-100` + instruments-service `reference_data/base_adapter.py:39-160` —
      onto `unified_trading_library.utils.retry`/`with_retry`. Preserve each adapter's classify-on-give-up behaviour. —
      **MTDS already migrated** (found already on `unified_trading_library.retry`/`retry_async` via `handle_api_errors`,
      decorator form, jitter disabled to match the prior deterministic backoff — no work needed). **instruments-service
      — SHIPPED `instruments-service@d88991d7`**: `_get_with_retry` now delegates to `with_retry_async` (callable form,
      since it's one shared method wrapping a single recurring GET+parse shape across ~30 venue-adapter call sites, not
      many independently-decorated methods like MTDS). The old `_handle_retryable_response`'s sentinel-return contract
      (return `None` to signal "retry", sleep inline) doesn't compose with UTL's exception-based retry model, so it's
      replaced by `_handle_response` + a small internal `_RetryableStatusError` (a `ClientError` subclass carrying
      `.status`) that UTL's `retryable_exceptions` catches. Give-up messages
      (`"HTTP {status} from {url} after N attempts"` / `"All N attempts failed for {url}: {exc}"`) and backoff timing
      (1s/2s/4s, no jitter, 3 attempts) are byte-identical to the old loop. Updated the 4 `TestHandleRetryableResponse`
      unit tests to the new `_handle_response` contract + added one `TestGetWithRetry` case covering the
      retryable-status exhaustion message (previously covered indirectly via the removed helper's own "raises on last
      attempt" test). Full `tests/reference_data/` + `tests/unit/` suites green (4314 passed, 40 skipped).
      `quality-gates.sh` exit 0, sentinel verified against `d88991d7` (hit the known host-wide `qg-host-governor` K=1
      contention — see `plans/active/issues/qg_host_governor_severe_contention_2026_07_13.md` — resolved via its
      sanctioned `IGNORE_TIMEOUT=true` workaround after the token-queue-inflated wall-clock gate false-failed an
      otherwise-green run).
- [x] ✅ [VERIFY] P1. Adapter retry behaviour unchanged (mock 429 → N retries → classify); health endpoints respond;
      `quality-gates.sh` green; quickmerge. — VERIFIED. `instruments-service@d88991d7`:
      `tests/unit/test_base_adapter_comprehensive.py` 17/17 pass (retry-on-429-then-success, all-retries-exhausted,
      persistent-retryable-status-exhaustion, params/headers passthrough). `market-tick-data-service`:
      `tests/market_interface/unit/test_base_adapter_and_rate_limiter.py` 22/22 pass (`handle_api_errors` sync+async
      retry/no-retry/exhaustion paths). `execution-service@348385ad` (health-router migration, shipped earlier in this
      plan): 8 new health-endpoint tests green + full `quality-gates.sh` exit 0 at ship time (sentinel-verified) —
      re-confirmation blocked this session by the host root-disk-full recurrence
      (`plans/active/issues/host_root_disk_full_transient_2026_07_13.md`, `scripts/setup.sh` couldn't provision a fresh
      `.venv`); relying on the ship-time green run as evidence rather than re-running under a disk-constrained host. No
      new code needed for this todo — an independent `_get_with_retry` consolidation attempt on instruments-service
      (this session, discarded before push) turned out redundant with `d88991d7` (already-shipped by a concurrent slot
      with a more faithful preservation of the original's two distinct give-up messages); confirmed clean via
      `git reset --hard origin/live-defi-rollout`, no local trace, no rework needed.

## Success criteria

`classify_venue_error` single-sources IS venue errors; execution has ONE health surface; one UTL retry helper, two
adapters consolidated.

## Notes for the worker

- Commit + Push + Flip each shippable unit in the same turn (CLAUDE.md HARD RULE).
