---
doc_type: plan
title: run-lifecycle-events-ssot
summary:
status: in_progress
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-service,
    execution-service,
    instruments-service,
    strategy-service,
    unified-trading-library,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-05
overview: 'Make every long-running entry-point in the workspace emit structured RUN_STARTED + RUN_COMPLETED|FAILED

  events via a single UTL helper, so monitors / observability / VM-watchdog can gate on the event stream

  rather than tail-grep raw logs. Closes the "no fire-and-forget VM launches" rule that just landed in

  CLAUDE.md (2026-05-05). Phased: UTL helper → audit → rollout → QG enforcement test.

  '
type: code
epic: observability
priority: P0
owner: Iggy
locked_by: live-defi-rollout
locked_since: 2026-05-05
completion_gates: { code: C5, deployment: D2, business: B1 }
repo_gates:
  - { repo: unified-trading-library, code: C0, deployment: D0, business: B0 }
  - { repo: market-tick-data-service, code: C0, deployment: D0, business: B0 }
  - { repo: market-data-processing-service, code: C0, deployment: D0, business: B0 }
  - { repo: instruments-service, code: C0, deployment: D0, business: B0 }
  - { repo: deployment-service, code: C0, deployment: D0, business: B0 }
  - { repo: feature-service-sports, code: C0, deployment: D0, business: B0 }
---

## Deferred work — migrated to: `plans/active/codex_violations_ratchet_to_five_2026_06_10.md` — successor:

codex_violations_ratchet_to_five_2026_06_10 (all 20 open items are shipped-but-unflipped: the UTL `run_lifecycle`
helper + tests, the audit + its findings, and the STEP 5.63/5.64 QG enforcement are all live in the codebase; the
per-repo rollout is now driven by the QG gate itself rather than a hand-maintained checklist, actively tracked in the
successor plan. The specific scripts named in the original plan — `migrate_sports_canonical.py`,
`feature-service-sports`, `risk-and-exposure-service` — are themselves stale/renamed/retired. No genuinely orphaned
items. NOTE: `locked_by: live-defi-rollout` was never cleared at archival — flagged for operator `[unlock-plan]`
cleanup.)

# Run-Lifecycle Events SSOT

## Context

The new CLAUDE.md rule **"No fire-and-forget VM launches (CRITICAL — production observability)"** mandates that every
long-running entry-point emit structured `STARTED` / progress / `STOPPED|FAILED` events to GCS so monitors can gate on
them, not on log-tail grep. Reference incident **2026-05-05**: 21 MDPS VMs ran and emitted `STARTED` + `STOPPED` cleanly
but produced 1440 empty placeholder bars per day per (venue, data_type) — events told the truth (presence of
STARTED/STOPPED) but absence of intermediate progress events with row counts (e.g. `INSTRUMENT_PROCESSED`) hid the
silent-success-with-zero-output failure mode.

This session (2026-05-05) discovered the same gap in `migrate_sports_canonical.py` — it emitted per-day
`MANIFEST_MIGRATION_SUMMARY` events but no run-level `RUN_STARTED` or terminal `RUN_COMPLETED|FAILED`, so monitors had
no clean handle on "did the migrate even start?" or "is it done?". Patched in MTDS `ce9b069` ad-hoc. **The audit found 4
peer MTDS migrate scripts (defi, polymarket, tradfi, cefi_v2) and 6 deployment-service entries with the same gap** —
fixing each ad-hoc would scatter the pattern. Better: a single UTL helper, applied uniformly, with QG enforcement so the
gap can't reopen.

The fix is a 4-phase plan: roll into UTL → verify every service is on UTL events → roll out the helper → enforce via QG
so future entry-points can't ship without it.

## Dependency DAG

```
Phase 1 (UTL helper + tests)
    │
    ▼
Phase 2 (audit: who's on UTL events vs roll-their-own)
    │
    ▼
Phase 3 (rollout: refactor every entry-point to use the helper) ───┐
    │                                                              │
    ▼                                                              │
Phase 4 (QG enforcement test) ◄────────────────────────────────────┘
    │
    ▼
DONE — every long-running script emits clean RUN_STARTED + RUN_COMPLETED|FAILED
```

## Phase 1 — UTL helper + unit tests [SEQUENTIAL]

Goal: a single context-manager API every script can call instead of hand-rolling start/end events.

API:

```python
from unified_trading_library.events import run_lifecycle

def main() -> int:
    with run_lifecycle(
        service_name="migrate-sports-canonical",
        details={"bucket": ..., "days_total": ..., "workers": 32, "dry_run": False},
    ) as run:
        # work
        for day in days:
            stats = process_day(day)
            run.update(rows_in=stats.rows_in, rows_out=stats.rows_out)
        # implicit RUN_COMPLETED with merged details + elapsed_s on clean exit
    return 0
    # implicit RUN_FAILED + re-raise on exception
```

Behavior:

- Auto-generates `run_id` (UTC timestamp + short uuid) and includes it in both events so monitors can correlate
  `STARTED` ↔ terminal pair.
- Event names derived from `service_name`: `migrate-sports-canonical` → `MIGRATE_SPORTS_CANONICAL_RUN_STARTED` /
  `MIGRATE_SPORTS_CANONICAL_RUN_COMPLETED` / `MIGRATE_SPORTS_CANONICAL_RUN_FAILED` (uppercase + dash→underscore +
  suffix).
- On enter: emit `{SERVICE}_RUN_STARTED` with `run_id` + supplied `details`. Capture `t0`.
- On clean exit: emit `{SERVICE}_RUN_COMPLETED` with `run_id` + merged `details` + `elapsed_s`.
- On exception exit: emit `{SERVICE}_RUN_FAILED` with `run_id` + `exception_type` + `exception_msg` (truncated to 500
  chars per UAC error-classification convention) + `elapsed_s` + merged `details`, then re-raise.
- `run.update(**kwargs)` merges into `details` for the terminal event (not re-emitted incrementally — those are separate
  progress events the script owns).

Files to add/edit:

- `unified-trading-library/unified_trading_library/events/run_lifecycle.py` — new module
- `unified-trading-library/unified_trading_library/events/__init__.py` — export `run_lifecycle`
- `unified-trading-library/tests/events/test_run_lifecycle.py` — new test file

Tests (in `tests/events/test_run_lifecycle.py`):

- [ ] [TEST] P0. STARTED emitted on enter with run_id + details.
- [ ] [TEST] P0. COMPLETED emitted on clean exit with same run_id + elapsed_s + merged details.
- [ ] [TEST] P0. FAILED emitted on exception with same run_id + exception_type + exception_msg + elapsed_s, exception
      re-raised.
- [ ] [TEST] P0. Same `run_id` across STARTED + terminal events (correlation).
- [ ] [TEST] P0. Event-name derivation: `migrate-sports-canonical` → `MIGRATE_SPORTS_CANONICAL_RUN_STARTED` etc.
- [ ] [TEST] P1. `run.update(...)` merges into terminal-event details.
- [ ] [TEST] P1. Long exception messages truncated to 500 chars.

Exit gates: UTL `quality-gates.sh` green, all new tests pass, helper exported from top-level
`unified_trading_library.events` package.

## Phase 2 — Audit [SEQUENTIAL after Phase 1]

Goal: list every long-running entry-point in the workspace and classify:

- **A.** Already uses UTL events (`setup_events` from `unified_trading_library.events`) — eligible for direct refactor
  in Phase 3.
- **B.** Uses a different events lib or rolls its own logging — needs migration to UTL events first.
- **C.** Has no events at all — needs both events setup AND lifecycle helper.

Audit method: grep + read frontmatter / `if __name__ == "__main__"` blocks across:

- All `*/scripts/*.py` (one-off scripts)
- All `*/{service}/{service}/__main__.py` (service CLIs)
- All `*/{service}/{service}/cli/*.py` (service CLI commands)
- VM launchers in `deployment-service/scripts/vm/*.sh` (these wrap Python entry-points; audit the Python target)

- [ ] [SCRIPT] P0. Run audit script, output a markdown table:
      `| repo | path | classification (A/B/C) | service_name | currently emits {STARTED,COMPLETED,FAILED}? |`. Persist
      to `unified-trading-pm/codex/05-infrastructure/run-lifecycle-events-audit-2026-05-05.md`.
- [ ] [ANALYSIS] P0. Sort by criticality (heavy-traffic services first: MTDS migrates, MDPS reprocessors,
      instruments-service backfill orchestrator, deployment-service scheduler).
- [ ] [DOC] P1. Document the SSOT (helper API + naming convention) in
      `/codex/06-coding-standards/observability-run-lifecycle.md` so new code lands compliant.

Exit gates: audit table committed, top-20 critical entry-points identified.

## Phase 3 — Rollout [PARALLEL by repo, after Phase 2]

Goal: every entry-point in the audit table uses `run_lifecycle`.

Per-repo work — each landed as one focused commit:

- [ ] [CODE] P0. **MTDS** — refactor `migrate_sports_canonical.py` (drop the ad-hoc events from `ce9b069`, replace with
      `run_lifecycle`). Then `migrate_defi_canonical.py`, `migrate_polymarket_canonical.py`,
      `migrate_tradfi_canonical.py`, `migrate_cefi_v2.py`. Plus any service `__main__.py` / forward-poll / VM-side
      entry-points that emit `setup_events` but no run lifecycle.
- [ ] [CODE] P0. **MDPS** — refactor `scripts/reprocess_sports_odds.py`, `scripts/seed_mock_data.py`,
      `scripts/smoke_matrix.py` if applicable, plus `__main__.py`.
- [ ] [CODE] P0. **instruments-service** — `scripts/full_polymarket_dump.py`,
      `scripts/migrate_local_sfi_to_canonical.py`, `scripts/reconcile_phantom_manifest_rows*.py`, plus orchestrator
      entry-point.
- [ ] [CODE] P0. **deployment-service** — `cluster.py`, `orchestrator.py`, `cli/main.py`, `vm/heartbeat_cli.py`,
      `scripts/vm/deployment_heartbeat.py`, `functions/rotate-exchange-keys/main.py`. Some of these are long-running
      services (heartbeat, orchestrator) — those should emit per-cycle progress events too, not just RUN_STARTED.
- [ ] [CODE] P1. **feature-service-sports** — service CLI entry-points + any backfill scripts.
- [ ] [CODE] P1. **execution-service / strategy-service / risk-and-exposure-service** — sweep CLIs.
- [ ] [QG] P0. Each repo's `quality-gates.sh` green after refactor.

Exit gates: every entry-point in the audit table calls `run_lifecycle`, no repo has the old hand-rolled
`log_event("..._RUN_STARTED", ...)` pattern remaining (search-and-prove).

## Phase 4 — QG enforcement test [SEQUENTIAL after Phase 3]

Goal: future entry-points can't ship without `run_lifecycle`.

Mechanism: add a structural check to **base-service.sh** (the cross-service QG enforcer that already gates
`ServiceBootstrap`, `Health API`, typed config reloaders, schema provenance, ApiKeyReloader per CLAUDE.md "Service
Infrastructure Requirements"). New STEP:

> **STEP 5.63 — Run-Lifecycle Events** — every Python entry-point that calls `setup_events(...)` must also use
> `run_lifecycle(...)` from `unified_trading_library.events` OR explicitly emit `{SERVICE}_RUN_STARTED` +
> `{SERVICE}_RUN_COMPLETED|FAILED` events. Detection: AST-walk the entry-point's main() and assert one of the patterns
> is present. Failure prints the script path + suggested helper invocation.

- [ ] [CODE] P0. Implement STEP 5.63 in `unified-trading-pm/scripts/quality-gates/base-service.sh` (or whichever script
      holds the cross-repo gates).
- [ ] [TEST] P0. Unit test for the structural check: a script with `setup_events` but no `run_lifecycle` fails the gate;
      a script with `run_lifecycle` passes.
- [ ] [DOC] P1. Update `/codex/06-coding-standards/observability-run-lifecycle.md` with the QG-enforced status.

Exit gates: base-service.sh STEP 5.63 fires correctly on every Phase-3-affected repo, and a synthetic broken-script test
fails it.

## Out of scope

- **Per-instrument progress events with row counts** — the new CLAUDE.md rule mentions this for adapters (e.g.
  `INSTRUMENT_PROCESSED`). That's a separate plan; this one is just run-level lifecycle. The two compose:
  `run_lifecycle` wraps the run; per-instrument events fire inside.
- **Cloud sink configuration for laptop runs** — `setup_events(mode="local")` keeps events in-process. VMs flip to cloud
  mode via env var. Out of scope here; we're standardizing the API, not the transport.
- **Existing-script deletion of hand-rolled lifecycle events** — `migrate_sports_canonical.py` ships ad-hoc events
  (commit `ce9b069`); the Phase 3 refactor will swap to the helper. Not a regression — the helper emits the same events
  with the same names.

## Critical files / SSOTs

- `unified-trading-pm/cursor-configs/CLAUDE.md` § "No fire-and-forget VM launches" — the rule that drives this
- `unified-trading-library/unified_trading_library/events/` — current events module (target for the helper)
- `unified-trading-pm/codex/06-coding-standards/` — destination for the new observability-run-lifecycle.md SSOT
- `unified-trading-pm/scripts/quality-gates/base-service.sh` — destination for STEP 5.63

## Verification

- After Phase 1: `cd unified-trading-library && bash scripts/quality-gates.sh` green;
  `from unified_trading_library.events import run_lifecycle` works; new tests pass.
- After Phase 2: audit markdown committed listing all entry-points + classifications.
- After Phase 3: `grep -rn 'RUN_STARTED' --include='*.py' --exclude-dir='.venv*'` finds only `run_lifecycle` callers (no
  hand-rolled `log_event("..._RUN_STARTED", ...)`).
- After Phase 4: base-service.sh STEP 5.63 fires on every affected repo; a synthetic broken-script integration test
  fails the QG.

## Notes for executing agents

- The currently-running migrate (`migrate_sports_canonical.py` PID 83704, started 2026-05-05 16:20:35Z) loaded the
  pre-fix script into Python memory and will finish on `ce9b069` ad-hoc events. Phase 3 will refactor away those ad-hoc
  events; future runs use the helper. Don't kill the running migrate.
- Keep the helper API small. Resist adding "progress event" methods on `RunContext` — those belong in domain code
  (`log_event` directly) and shouldn't be coupled to the lifecycle wrapper.
- Match existing UTL events naming conventions (uppercase + underscores). The `service_name` → event-prefix derivation
  must match the existing ad-hoc emissions (`MIGRATE_SPORTS_CANONICAL_RUN_STARTED` etc.) so monitors don't break.
