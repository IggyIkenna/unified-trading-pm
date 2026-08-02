---
doc_type: plan
title: Finalize — instruments-service E2E live/mock/observability (Phases 5-7) close-out
summary: >-
  Gated close-out twin for `instruments_service_e2e_live_mock_observability_2026_07_27.md`, which was reclassified
  `assigned_vm: NA → planning` by the 2026-07-30 `/na-eligibility-audit cross-cutting` run. Holds the archival ritual +
  the post-run reconciliation that must happen once that plan's 4 verification todos (Phase 5 live-mode clock alignment,
  Phase 6 mock-mode failure scenarios, Phase 7 observability, and the 2026-03-23 six-bug re-verify) have all run and
  been evidenced. Stays `status: draft` until the source plan's last todo flips.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer]
tags: [ao-dispatch, close-out, reclassification, na-audit, e2e-testing, instruments-service]
related:
  [
    /plans/active/instruments_service_e2e_live_mock_observability_2026_07_27.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-07-30
last_updated: 2026-07-30
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: none
depends_on: [instruments_service_e2e_live_mock_observability_2026_07_27]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  /na-eligibility-audit cross-cutting, 2026-07-30 — RECLASSIFY verdict on
  instruments_service_e2e_live_mock_observability_2026_07_27.md (Phase-2 conflict-check CLEAR: the only citation is the
  cross-cutting consolidated closeout's digest, which the shared conflict-check SSOT § 3 explicitly defines as a digest,
  not a dispatch claim).
context_scope:
  [
    /plans/active/instruments_service_e2e_live_mock_observability_2026_07_27.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
  ]
---

# Finalize — instruments-service E2E live/mock/observability close-out

> **Gated twin** (`gate_on_depends: true`). Do NOT start until every todo in
> [`/plans/active/instruments_service_e2e_live_mock_observability_2026_07_27.md`](/plans/active/instruments_service_e2e_live_mock_observability_2026_07_27.md)
> is `- [x]` with cited evidence. Authored by the 2026-07-30 `/na-eligibility-audit` reclassification pass per
> [`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`](/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md)
> § 1(b) — retroactive reclassification keeps the source doc's name and gains this bolt-on finalize sibling.

## Why this exists

The source plan re-scopes Phases 5-7 of the archived 2026-03 instruments-service E2E audit. Its 4 todos are bounded
verification RUNS with explicit per-item done-when checklists, which is why the NA audit reclassified it. But a
verification pass that finds real defects must not silently end at "ran the checks" — this twin holds the reconciliation
that turns those findings into tracked work and closes the plan properly.

## Todos

- [x] ✅ [REVIEW] P2. **Reconcile every Phase 5/6/7 sub-check against its recorded outcome.** For each numbered
      sub-check (5.1-5.4, 6.1-6.7, 7.1-7.6) confirm the source plan records a PASS/FAIL verdict with the command that
      produced it — not a blanket "phase green". Any sub-check that could not be run (e.g. a scenario the current CLI no
      longer supports) is recorded as an explicit honest-absence with its reason, never silently dropped. **Done when**:
      every one of the 17 sub-checks has a recorded verdict + evidence in the source plan. Repo: unified-trading-pm. —
      **DONE 2026-08-01.** Reconciled all 17 sub-checks against the definitions in the archived original
      (`/plans/archive/2026_07/e2e_testing_001_instruments_service_2026_03_22.md` lines 88-116) vs. what the source
      plan's Phase 5/6/7 todos + Progress Log actually recorded. Verdict: **17/17 have a recorded verdict + evidence, 0
      silently dropped.** Full reconciliation table below.
- [x] ✅ [REVIEW] P2. **Triage the [VALIDATE] P3 six-bug re-verify outcome.** The source plan's last todo re-checks the
      6 bugs from the 2026-03-23 DEFI E2E audit (Balancer 400, Aster lowercase-category, Hyperliquid 0-instruments,
      missing data-catalogue entries, a Pydantic warning, CFE-not-in-UAC). Per the findings-triage HARD RULE, each bug
      that is STILL real becomes a tracked `- [ ]` todo (in the source plan if in-scope, else
      `plans/active/issues/<slug>_<date>.md`) — never prose, never a re-filed duplicate of an already-open issue doc
      (grep `plans/active/issues/` first). **Done when**: each of the 6 is recorded as fixed-incidentally /
      still-real-and-now-tracked / no-longer-applicable, with the tracking location named. Repo: unified-trading-pm. —
      **DONE 2026-08-01.** Triage table below; grepped `plans/active/issues/` for a duplicate on each bug's topic — 0
      hits on any of the 6. **Net: 0 of 6 are still-real; 0 new todos filed.**
- [ ] [PLANNING] P3. **Archive the source plan per the 6-step ritual.** Once both reviews above are done and the source
      plan has zero open todos and no `locked_by:`, run the standard archival ritual from
      [`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`](/codex/12-agent-workflow/plan-completion-and-archival-discipline.md)
      (dated archive folder, `status: complete`, every corpus referrer repointed, inventory regenerated), then archive
      this finalize twin alongside it. **Done when**: both docs are under `plans/archive/2026_07/` and
      `regenerate_active_plan_inventory.py` reports 0 new orphans. Repo: unified-trading-pm.

## Sub-check reconciliation (Phase 5/6/7, todo 1)

Definitions per the archived original (`/plans/archive/2026_07/e2e_testing_001_instruments_service_2026_03_22.md` lines
88-116); verdicts + evidence per the source plan's Phase 5/6/7 todos and Progress Log
(`/plans/active/instruments_service_e2e_live_mock_observability_2026_07_27.md` — now fully `[x]`, see that doc for the
full command transcripts this table summarizes).

| #   | Sub-check                                              | Verdict                 | Evidence summary                                                                                                                                                                                                                                                                                                        |
| --- | ------------------------------------------------------ | ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 5.1 | 15-min boundary-wait loop                              | N/A (honest-absence)    | Literal `--interval`/`--operation live --mode batch` flags don't exist (confirmed `--help` + full-repo grep); architecture never implemented a wall-clock-aligned wait for this service — not a regression.                                                                                                             |
| 5.2 | Runs at :00/:15/:30/:45                                | N/A (honest-absence)    | Same root cause as 5.1 — no internal alignment loop exists to test; `UTCAlignedScheduler` is MTDS-only.                                                                                                                                                                                                                 |
| 5.3 | UEI STARTED/per-venue COMPLETED-FAILED/final COMPLETED | PASS, premise-corrected | `main_service_cli(--operation instruments --mode live --asset-group cefi)` under `CLOUD_MOCK_MODE=true`: `ServiceRuntime` STARTED confirmed + per-venue fetch logging confirmed; no discrete per-venue `COMPLETED` event exists in the shipped taxonomy (counter/completeness-based design instead) — noted, not a bug. |
| 5.4 | Ctrl-C/SIGTERM graceful shutdown, no partial writes    | FAIL → FIXED → PASS     | Found real `AttributeError` crash on SIGTERM (uncaught in `cleanup()`'s coordination-event call under mock+live mode); fixed `instruments-service@518cc7a7`; re-verified via a mid-run SIGTERM against HYPERLIQUID (`SystemExit code=0`, no traceback).                                                                 |
| 6.1 | Normal mock generation                                 | PASS                    | `--venues BYBIT-SPOT` under `CLOUD_MOCK_MODE=true`: `URDI[BYBIT-SPOT]: fetched 3314 instruments`, no crash.                                                                                                                                                                                                             |
| 6.2 | Stress/10x cardinality                                 | Honest-absence          | No volume/cardinality knob exists anywhere (`--scenario` is a complete no-op) — documented, not fabricated.                                                                                                                                                                                                             |
| 6.3 | `missing_data` mid-day disappearance                   | Honest-absence          | No disappear-mid-run hook exists; live Hyperliquid attempt was rate-limited/inconclusive. Real-world analogue chased down instead in the P3 six-bug re-verify (Bug 3: Hyperliquid is no longer a DEFI venue at all — premise superseded).                                                                               |
| 6.4 | Fake symbol injection                                  | Honest-absence          | No `FAKE-EXCHANGE`/`NOSYMBOL` hook exists via CLI (0 grep hits); would need a unit-level monkeypatch, out of a run-and-verify SCRIPT todo's scope.                                                                                                                                                                      |
| 6.5 | Missing entire category (DEFI)                         | PASS                    | `get_venues_for_asset_groups` scopes strictly to requested groups; the 6.1 run (cefi-only) shows zero DEFI references anywhere in the log.                                                                                                                                                                              |
| 6.6 | Corrupt expiry dates                                   | PASS, premise-corrected | `_parse_expiry("not-a-date")` → `None` in all 3 real parsers, confirmed live — doesn't crash; none of them log a warning (silent-skip design) — noted, not a bug.                                                                                                                                                       |
| 6.7 | `config_source` check                                  | PASS                    | `ServiceRuntime.config_source` is a pure derived property (`"local" if is_mock else "gcs"`); the 6.1 run's `data=mock` confirms `is_mock=True` → `config_source="local"`.                                                                                                                                               |
| 7.1 | ServiceRuntime log line, all dimensions                | PASS, premise note      | Log line covers 7 of ~15 dataclass fields; every field it documents itself as covering is present and confirmed live twice.                                                                                                                                                                                             |
| 7.2 | UEI STARTED/COMPLETED/per-venue events                 | PASS, premise note      | Lifecycle is STARTED/STOPPED/FAILED (not COMPLETED) plus an aggregate `PROCESSING_STARTED`/`PROCESSING_COMPLETED` pair — confirms + extends 5.3's finding, not a gap.                                                                                                                                                   |
| 7.3 | Shard-level isolation                                  | PASS                    | Two independent live reproductions (HYPERLIQUID 429 retry-recovers; `FAKE-EXCHANGE-SPOT` no-adapter-registered) — both leave the other venues fetching/writing normally, exit=0, gap surfaced via `SHARD_INCOMPLETE`/`PUBLISHED_DEGRADED`, never a crash or silent partial-success.                                     |
| 7.4 | Dry-run warning                                        | PASS, exact match       | Both `WARNING DRY RUN — no cloud writes will be performed` and `WARNING UCI dry-run mode ACTIVE` confirmed live.                                                                                                                                                                                                        |
| 7.5 | `ADAPTER_FETCH_FAILED` classification                  | PASS                    | HYPERLIQUID 429 correctly classified (`error_code=RATE_LIMIT, action=retry, retry_safe=true` via UAC `classify_venue_error()`); the no-adapter-registered case correctly does NOT emit it (distinct failure mode — nothing was fetched to classify).                                                                    |
| 7.6 | Memory watchdog logged                                 | PASS, exact match       | `Memory watchdog started for instruments-service (threshold=85.0%)` confirmed live during `ServiceBootstrap`.                                                                                                                                                                                                           |

**Net: 17/17 sub-checks have a recorded verdict + evidence in the source plan. 0 silently dropped.** Breakdown: 11 PASS
(5 with a premise correction — the check as originally worded didn't exactly match the shipped design, but the
underlying behavior was verified and is not a bug), 1 FAIL→FIXED→PASS (5.4, the one genuine regression this verification
pass found), 5 honest-absence/N/A (5.1, 5.2, 6.2, 6.3, 6.4 — each with a stated, non-fabricated reason the check could
not be run as literally specified). No further action needed for this todo; nothing here requires a new tracked fix
(5.4's fix already shipped and is captured in the source plan's own todo).

## Six-bug re-verify triage (2026-03-23 DEFI E2E audit, todo 2)

Source of the 6 bugs: `/plans/archive/2026_07/e2e_testing_001_instruments_service_2026_03_22.md` lines 158-163 (the real
2026-03-23 DEFI-category audit run). Verdicts + evidence per the source plan's `[VALIDATE]` P3 todo and Progress Log
entry (`slot-6 2026-08-01`).

| Bug | Original finding                                        | Triage disposition       | Tracking location                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| --- | ------------------------------------------------------- | ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Balancer 400 Bad Request (P1)                           | **fixed-incidentally**   | None needed — `_BALANCER_API` already carries `/graphql` (confirmed via `git log -S` present since the earliest surviving commit `7fa77592`), plus live curl replay + a live CLI run both succeeded. Evidence in source plan Progress Log.                                                                                                                                                                                                                      |
| 2   | Aster lowercase `defi/ASTER` category (P2)              | **no-longer-applicable** | None needed — Aster is no longer a DeFi venue at all (UAC `VENUE_CATEGORY_MAP: ASTER → "cefi"`; adapter lives under `adapters/cefi/`); the casing convention itself is now derived architecture-wide via `asset_group_key()`, so the described inconsistency class cannot recur. Evidence in source plan Progress Log.                                                                                                                                          |
| 3   | Hyperliquid 0 instruments in DEFI (P2)                  | **no-longer-applicable** | None needed — same reclassification as Bug 2: `VENUE_CATEGORY_MAP: HYPERLIQUID → "cefi"`, no `adapters/defi/hyperliquid.py`, confirmed deliberate via UAC's `_defi.py` capability-declaration comment. Evidence in source plan Progress Log.                                                                                                                                                                                                                    |
| 4   | Missing `dataset_id` catalogue entries (P3)             | **no-longer-applicable** | None needed — the `dataset_id`-keyed catalogue schema this bug referenced no longer exists (replaced by `shard_status:` keying); the validation/warning mechanism itself has 0 grep hits fleet-wide. Confirmed via 3 live mock-mode runs, zero catalogue warnings. Evidence in source plan Progress Log.                                                                                                                                                        |
| 5   | Pydantic `model_copy()` UserWarning (P3)                | **no-longer-applicable** | None needed — confirmed unreachable: `project_id`/`gcp_project_id` alias to the identical env var, so the guard that would trigger the warning-causing branch can never pass (0 warnings across 3 live runs + a direct instantiation under `warnings.catch_warnings`). The dead `model_copy()` branch itself is a pre-existing minor style nit, not a live bug — not filed as a new todo (no observable behavior to fix). Evidence in source plan Progress Log. |
| 6   | `CFE` venue not in UAC `INSTRUMENT_TYPES_BY_VENUE` (P3) | **fixed-incidentally**   | None needed — venue renamed to `CBOE` fleet-wide, fully registered in every UAC venue table; confirmed live (`--venues CBOE --dry-run` clean, zero "not in UAC" warnings). Evidence in source plan Progress Log.                                                                                                                                                                                                                                                |

**Net: 0 of 6 still-real, 0 new todos filed** — consistent with the source plan's own "4 months have passed, some may
already be fixed incidentally" framing. Grepped `plans/active/issues/` for each bug's topic (balancer, aster,
hyperliquid, catalogue, pydantic, cfe/cboe) before concluding — 0 duplicate open issue docs found for any of the 6.

## Codex SSOTs

- [`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`](/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md)
  — the naming/pairing convention this doc follows and the conflict-check that cleared the reclassification.
- [`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`](/codex/12-agent-workflow/plan-completion-and-archival-discipline.md)
  — the 6-step archival ritual todo 3 runs.
- [`/codex/04-architecture/shard-level-failure-isolation.md`](/codex/04-architecture/shard-level-failure-isolation.md) —
  the shard-isolation contract Phase 7's check 7.3 verifies.

## Progress Log

- **2026-07-30** — Authored by the `/na-eligibility-audit cross-cutting` tranche run as the paired finalize twin for the
  `NA → planning` reclassification of `instruments_service_e2e_live_mock_observability_2026_07_27.md`. No work executed
  here; `status: draft` + `gate_on_depends: true` hold it until the source plan's todos land.
- **slot 3 (review-role worker) 2026-08-01 — todo 1 DONE.** Gate confirmed satisfied first (source plan: 0 open `- [ ]`,
  no `locked_by`). Reconciled all 17 Phase 5/6/7 sub-checks against the archived original's definitions and the source
  plan's recorded outcomes — 17/17 have a verdict + evidence, 0 silently dropped (11 PASS incl. 5 premise-corrected, 1
  FAIL→FIXED→PASS, 5 honest-absence/N/A). Full table added above. Todos 2 (six-bug triage) and 3 (archival) are separate
  backlog items, not touched by this task.
- **slot 3 (review-role worker) 2026-08-01 — todo 2 DONE.** Triaged all 6 bugs from the source plan's `[VALIDATE]`
  re-verify against the findings-triage HARD RULE: 2 fixed-incidentally (Balancer 400, CFE→CBOE rename), 4
  no-longer-applicable (Aster/Hyperliquid reclassified out of DEFI, catalogue validation mechanism removed, Pydantic
  warning path unreachable). 0 still-real, 0 new todos filed — grepped `plans/active/issues/` per bug topic first, 0
  duplicates found. Full table added above. Todo 3 (archival) is a separate backlog item.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
